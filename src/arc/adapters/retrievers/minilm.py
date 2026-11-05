from hashlib import file_digest
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = "cross-encoder/ms-marco-MiniLM-L6-v2"
MODEL_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
MAX_LENGTH = 512
MODEL_FILES = {
    "config.json": "380e02c93f431831be65d99a4e7e5f67c133985bf2e77d9d4eba46847190bacc",
    "model.safetensors": "821d1aa69520101d6e0737f78a042ae25b19e5cb9160701909d10434f4aeb0ae",
    "special_tokens_map.json": "3c3507f36dff57bce437223db3b3081d1e2b52ec3e56ee55438193ecb2c94dd6",
    "tokenizer_config.json": "a5c2e5a7b1a29a0702cd28c08a399b5ecc110c263009d17f7e3b415f25905fd8",
    "tokenizer.json": "d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66",
    "vocab.txt": "07eced375cec144d27c900241f3e339478dec958f92fddbc551f295c992038a3",
}


class MiniLMReranker:
    revision = MODEL_REVISION

    def __init__(self, model_path: Path, device: str, batch_size: int = 32) -> None:
        if model_path.name != MODEL_REVISION or batch_size < 1:
            raise ValueError("Expected pinned MiniLM snapshot and positive batch size")
        for name, expected in MODEL_FILES.items():
            with (model_path / name).open("rb") as stream:
                if file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError(f"MiniLM snapshot fingerprint mismatch: {name}")
        torch.manual_seed(20261105)
        self.device = device
        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True, trust_remote_code=False
        )
        self.model = (
            AutoModelForSequenceClassification.from_pretrained(
                model_path, local_files_only=True, trust_remote_code=False, use_safetensors=True
            )
            .to(device)
            .eval()
        )
        if next(self.model.parameters()).dtype != torch.float32:
            raise ValueError("MiniLM parameters must be float32")

    def score(self, query: str, passages: list[str]) -> tuple[list[float], int]:
        scores = []
        truncated = 0
        with torch.inference_mode():
            for start in range(0, len(passages), self.batch_size):
                batch = passages[start : start + self.batch_size]
                queries = [query] * len(batch)
                raw = self.tokenizer(queries, batch, truncation=False, verbose=False)
                truncated += sum(len(tokens) > MAX_LENGTH for tokens in raw["input_ids"])
                tokens = self.tokenizer(
                    queries,
                    batch,
                    padding=True,
                    truncation="longest_first",
                    max_length=MAX_LENGTH,
                    return_tensors="pt",
                ).to(self.device)
                scores.extend(self.model(**tokens).logits.flatten().cpu().tolist())
        return scores, truncated
