import os
import pandas as pd
import torch
import faiss
import numpy as np
from PIL import Image
from glob import glob
from torch.utils.data import Dataset
from tqdm import tqdm
from torchvision.transforms import Resize, Pad, CenterCrop, Compose


column_to_words = {
    "article_id": "Article ID",
    "prod_name": "Product Name",
    "product_type_name": "Product Type",
    "perceived_colour_value_name": "Colour Value",
    "perceived_colour_master_name": "Colour",
    "index_name": "Garment type",
    "department_name": "Store Department",
    "index_group_name": "Group",
    "section_name": "Store Section",
    "garment_group_name": "Garment Group",
    "detail_desc": "Garment Description",
}


def row_to_sentences(row):
    """Turns rows of a dataframe into a list of sentences. Each sentence is a string that contains all the
    information of a row but in a readable sentence format.
    For example: "Article ID: 123456; Product Name: T-shirt; Product Type: Shirt; Colour Value: Red; ..."
    """
    sentence = f"It is a {str(row['product_type_name']).rstrip('.')}; "
    sentence += f"Colour: {row['perceived_colour_value_name']} {str(row['perceived_colour_master_name']).rstrip('.')}; "
    sentence += f"Description: {str(row['detail_desc']).rstrip('.')}; "
    sentence += f"Product Name: {str(row['index_name']).rstrip('.')}; "
    sentence += f"Store Department: {str(row['department_name']).rstrip('.')}."
    return sentence


class HMDataset(Dataset):
    def __init__(self, root):
        self.root = root
        self.data = self.load_data()

        self.image_transform = Compose(
            [
                Resize(size=224, max_size=244),
                Pad(244, fill=255),
                CenterCrop(224),
                lambda x: torch.tensor(np.array(x)),
            ]
        )

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]
        article_id = row["article_id"]
        img = Image.open(self.id_to_path[article_id]).convert("RGB")
        image = self.image_transform(img)
        text = row_to_sentences(row)
        return {"image": image, "text": text, "article_id": article_id}

    def load_data(self):
        df = pd.read_csv(os.path.join(self.root, "articles.csv"))
        # keep only the columns of interest
        self.data = df[list(column_to_words.keys())]

        # filter only womens articles
        self.filter_data_with_query("section_name", "Women|women")

        # load image paths
        self.id_to_path = {}
        for img_path in glob(os.path.join(self.root, "images/*/*")):
            id = int(img_path.split("/")[-1].split(".")[0])
            self.id_to_path[id] = img_path
        self.filter_data_by_article_ids(list(self.id_to_path.keys()))
        print("Data loaded with", len(self.data), "articles.")
        return self.data

    def filter_data_with_query(self, column, query):
        self.data = self.data[self.data[column].str.contains(query)]
        return self.data

    def filter_data_by_article_ids(self, article_ids):
        self.data = self.data[self.data["article_id"].isin(article_ids)]
        return self.data

    def get_image_path_from_article_id(self, article_id):
        return self.id_to_path[article_id]

    def get_image_from_article_id(self, article_id):
        return Image.open(self.get_image_path_from_article_id(article_id)).convert("RGB")


class FaissDatabase:
    def __init__(self, article_ids, embeddings=None, index=None):
        assert embeddings is not None or index is not None, "Either embeddings or index should be provided."
        if index is None:
            self.index = faiss.IndexFlatIP(embeddings.shape[-1])
            self.index.add(embeddings)
        else:
            self.index = index
        self.article_ids = article_ids

    @classmethod
    def from_dataset(cls, dataset, model, field="text", batch_size=1):
        assert field in ["text", "image"]
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=False)
        embeddings_list, article_ids = [], []
        for batch in tqdm(dataloader):
            if field == "text":
                embeddings_list.append(model.embed_text(batch["text"], return_tensor="np"))
            else:
                embeddings_list.append(model.embed_image(batch["image"], return_tensor="np"))
            article_ids.append(batch["article_id"][0])
        return cls(embeddings=np.stack(embeddings_list), article_ids=article_ids)

    @classmethod
    def from_dump(cls, folder):
        index = faiss.read_index(os.path.join(folder, "index.faiss"))
        article_ids = np.load(os.path.join(folder, "article_ids.npy")).tolist()

        num_articles = len(article_ids)
        assert num_articles == index.ntotal, "Number of article_ids should match the number of embeddings."
        print(f"Database loaded with {num_articles} articles.")
        return cls(article_ids, index=index)

    def search(self, query_embedding, k=1, return_article_ids=False):
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        elif query_embedding.ndim == 2:
            assert query_embedding.shape[0] == 1, "Batch search is not supported."
        else:
            raise ValueError("Query embedding should be 1D or 2D array.")
        _, indices = self.index.search(query_embedding, k)
        if return_article_ids:
            return [self.article_ids[i] for i in indices[0]]
        return indices[0]

    def dump(self, folder):
        os.makedirs(folder, exist_ok=True)
        faiss.write_index(self.index, os.path.join(folder, "index.faiss"))
        np.save(os.path.join(folder, "article_ids.npy"), np.array(self.article_ids))
