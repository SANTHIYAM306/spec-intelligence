"""Optional local-only LLM synthesis over retrieved evidence with citation-ID validation."""
from __future__ import annotations
import json, re
from typing import Any
from .answer import INSUFFICIENT, format_citation

def build_grounded_prompt(question: str, evidence: list[dict[str, Any]]) -> str:
    blocks = []
    for i, item in enumerate(evidence, 1):
        blocks.append(f"EVIDENCE {i} | element_id={item.get('element_id')}\n"
                      f"CITATION={format_citation(item)}\nTEXT={str(item.get('text',''))[:5000]}")
    return (
      "You answer engineering questions using ONLY the evidence below. Do not use prior knowledge. "
      "If evidence is insufficient or conflicting, return decline=true and no claims. "
      "Every claim must cite one or more exact element_id values from the evidence. "
      "Return valid JSON only with schema: "
      '{"decline": boolean, "reason": string, "claims": [{"text": string, "element_ids": [string]}]}. '
      "Never invent element IDs, numeric values, revision details, or page references.\n\n"
      f"QUESTION:\n{question}\n\nEVIDENCE:\n" + "\n\n".join(blocks)
    )

def validate_generated_payload(payload: dict[str, Any], evidence: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    errors = []
    allowed = {str(x.get("element_id")) for x in evidence}
    if not isinstance(payload.get("decline"), bool): errors.append("decline must be boolean")
    if not isinstance(payload.get("claims"), list): errors.append("claims must be a list")
    for i, claim in enumerate(payload.get("claims", [])):
        if not isinstance(claim, dict) or not isinstance(claim.get("text"), str) or not claim.get("text", "").strip():
            errors.append(f"claims[{i}] must have non-empty text")
            continue
        ids = claim.get("element_ids")
        if not isinstance(ids, list) or not ids: errors.append(f"claims[{i}] needs element_ids")
        elif any(str(x) not in allowed for x in ids): errors.append(f"claims[{i}] references an unknown element_id")
    if payload.get("decline") is False and not payload.get("claims"):
        errors.append("non-declined answer needs at least one claim")
    if payload.get("decline") is True and payload.get("claims"):
        errors.append("declined answer must not contain claims")
    return not errors, errors

def answer_with_local_llm(question: str, evidence: list[dict[str, Any]], model_path: str,
                          local_files_only: bool = True, max_new_tokens: int = 450) -> dict[str, Any]:
    """Generate JSON claims using a locally available Transformers causal LM.

    Model weights are not downloaded by default. If model loading/generation fails, raise a
    clear exception so the caller can use the evidence-excerpt fallback.
    """
    if not evidence:
        return {"answer": INSUFFICIENT, "citations": [], "declined": True, "evidence": [],
                "generation_mode": "local_llm"}
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError('Local LLM generation needs: pip install -e ".[llm]"') from exc
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=local_files_only,
                                               trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=local_files_only,
                                                  trust_remote_code=False, device_map="auto")
    prompt = build_grounded_prompt(question, evidence)
    if hasattr(tokenizer, "apply_chat_template"):
        messages = [{"role": "system", "content": "Follow the evidence-only JSON output contract exactly."},
                    {"role": "user", "content": prompt}]
        input_ids = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                                   return_tensors="pt")
        inputs = {"input_ids": input_ids.to(model.device)}
        if tokenizer.pad_token_id is not None: inputs["attention_mask"] = torch.ones_like(input_ids).to(model.device)
    else:
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                                pad_token_id=tokenizer.eos_token_id)
    input_length = inputs["input_ids"].shape[1]
    decoded = tokenizer.decode(output[0][input_length:], skip_special_tokens=True).strip()
    match = re.search(r"\{.*\}", decoded, flags=re.S)
    if not match: raise ValueError("Local model did not return a JSON object")
    payload = json.loads(match.group(0))
    valid, errors = validate_generated_payload(payload, evidence)
    if not valid: raise ValueError("Local model output failed evidence validation: " + "; ".join(errors))
    if payload["decline"]:
        return {"answer": INSUFFICIENT + " Reason: " + str(payload.get("reason", "evidence was insufficient")),
                "citations": [], "declined": True, "evidence": [], "generation_mode": "local_llm"}
    by_id = {str(x.get("element_id")): x for x in evidence}
    claims, citations, used_evidence = [], [], []
    for claim in payload["claims"]:
        claim_citations = []
        for eid in claim["element_ids"]:
            record = by_id[str(eid)]
            citation = format_citation(record)
            claim_citations.append(citation)
            if citation not in citations: citations.append(citation)
            if record not in used_evidence: used_evidence.append(record)
        claims.append(str(claim["text"]).strip() + " " + " ".join(claim_citations))
    return {"answer": "\n".join(claims), "citations": citations, "declined": False,
            "evidence": [{"element_id": x.get("element_id"), "text": x.get("text"),
                          "citation": format_citation(x)} for x in used_evidence],
            "generation_mode": "local_llm", "claims": payload["claims"]}
