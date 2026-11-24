"""
Compartilha publicamente o dataset de avaliação (e os experimentos rodados contra ele).
Rode uma vez e guarde o link: compartilhar de novo gera um link diferente.
"""

import os
from dotenv import load_dotenv
from langsmith import Client

load_dotenv()

dataset_name = f"{os.getenv('LANGSMITH_PROJECT')}-eval"
print(Client().share_dataset(dataset_name=dataset_name)["url"])
