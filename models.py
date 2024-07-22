import torch
from transformers import AutoImageProcessor, AutoModel, AutoTokenizer
import torch.nn.functional as F
import os


os.environ["TOKENIZERS_PARALLELISM"] = "false"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def get_model(model_name="laion/CLIP-ViT-bigG-14-laion2B-39B-b160k"):
    model = AutoModel.from_pretrained(model_name)
    if device == "cuda":
        model = model.to(device)
        model = model.half()
    processor = AutoImageProcessor.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, processor, tokenizer


class ClipModel:
    def __init__(self, model_name="laion/CLIP-ViT-bigG-14-laion2B-39B-b160k"):
        self.model, self.processor, self.tokenizer = get_model(model_name)
        self.model.to(device)
        self.model.eval()

    def embed_image(self, img, return_tensor="pt"):
        with torch.no_grad():
            pixel_values = self.processor(img, return_tensors="pt")["pixel_values"].to(device)
            features = self.model.get_image_features(pixel_values)[0]
            features = F.normalize(features, p=2, dim=-1).cpu()
        return features.numpy() if return_tensor == "np" else features

    def embed_text(self, t, return_tensor="pt"):
        with torch.no_grad():
            features = self.model.get_text_features(
                **self.tokenizer(t, truncation=True, return_tensors="pt").to(device)
            )[0]
            features = F.normalize(features, p=2, dim=-1).cpu()
        return features.numpy() if return_tensor == "np" else features
