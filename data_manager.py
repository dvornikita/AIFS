from dataset import HMDataset, FaissDatabase
from models import ClipModel


class DataManager:
    def __init__(self, dataset_root, database_root=None, model=None):
        self.dataset = HMDataset(dataset_root)

        if database_root:
            self.database = FaissDatabase.from_dump(database_root)
        else:
            print("Initializing database from dataset.")
            self.database = FaissDatabase.from_dataset(self.dataset, self.model, field="image")

        self.model = model if model else ClipModel()

    def get_image_path_from_text_query(self, query, k=1):
        query_embedding = self.model.embed_text(query, return_tensor="np")
        article_id = self.database.search(query_embedding, k=1, return_article_ids=True)[0]
        return self.dataset.get_image_path_from_article_id(article_id)

    def get_image_path_from_image_query(self, img, k=1):
        query_embedding = self.model.embed_image(img, return_tensor="np").reshape(1, -1)
        article_id = self.database.search(query_embedding, k=1, return_article_ids=True)[0]
        return self.dataset.get_image_from_article_id(article_id)
