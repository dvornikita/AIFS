# AIFS: AI Fashion Stylist as a multi-modal ChatBot
This implements AIFS to get garment recommendations for the product in the database via interacting with a chatbot.

## What is suported
Right now, the chatbot supports the following scenarios:
1) Seasonal recomendations,
2) Event-based recommendations,
3) Image-based recommendations.
4) Try-on of garment on Taylor Swift
4) Image-to-video for the generated Taylor Swift

## What is not supported
Due to the lack of time, the repository does not support the following scenarios:
1) Similarity-based recommendations,
2) Video output quality can be improved. Or now one can also use [this](https://lumalabs.ai/dream-machine/creations).

## Preparations
1) Make sure you have the H&M dataset downloaded.
2) Download the feature database from [here](https://drive.google.com/file/d/1O2nxM_j58_7-RrZM9sGGvT54AUl2W-iB/view?usp=sharing).
It contains CLIP embeddings of the images in the dataset.

## How to run
1) Create your environment with conda or venv. Here is an example of how to do it with conda:
```bash
    conda create --name aifs_env python=3.11
```
2) Install the packages there from `requirements.txt`:
```bash
    conda activate aifs_env
    pip install -r requirements.txt
```
3) Run the notebook `notebook.ipynb` in the root directory of the repository (using the same envitonment).
4) Set the path to the dataset and your api key there.
5) Run everything in the notebook. 