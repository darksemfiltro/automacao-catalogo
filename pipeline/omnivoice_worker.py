"""Worker portátil: execute com Python que tenha o pacote oficial omnivoice."""
import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True)
    p.add_argument("--model", default="k2-fsa/OmniVoice")
    p.add_argument("--device", default=None)
    a = p.parse_args()
    import numpy as np
    import soundfile as sf
    import torch
    from omnivoice.models.omnivoice import OmniVoice
    from omnivoice.utils.common import get_best_device
    data = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    device = a.device or get_best_device()
    model = OmniVoice.from_pretrained(a.model, device_map=device,
                                     dtype=torch.float16 if device == "cuda" else torch.float32)
    for s in data["segments"]:
        torch.manual_seed(int(s.get("seed", 90000)))
        audio = model.generate(text=s["text"], language=s.get("language", data.get("language", "Portuguese")),
            ref_audio=s.get("ref_audio", data.get("ref_audio")), ref_text=s.get("ref_text", data.get("ref_text")),
            speed=s.get("speed", 1.0), num_step=32, guidance_scale=2.0)[0]
        if hasattr(audio, "detach"):
            audio = audio.detach().cpu().numpy()
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)
        gap = float(s.get("gap_after", 0))
        if gap:
            audio = np.concatenate([audio, np.zeros(int(model.sampling_rate * gap), dtype=np.float32)])
        dest = Path(s["output"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        sf.write(dest, audio, model.sampling_rate, subtype="PCM_16")
        print(s["id"], len(audio) / model.sampling_rate)


if __name__ == "__main__":
    main()
