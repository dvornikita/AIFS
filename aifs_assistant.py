from typing import Optional
import os
from PIL import Image
from IPython.display import display
from openai import OpenAI
from prompts import get_scenario_instruction
from enum import Enum
from data_manager import DataManager
from caption import caption_image
from image_generation import generate_image


class Scenario(Enum):
    SCENARIO_1 = 1
    SCENARIO_2 = 2
    SCENARIO_3 = 3


def get_client(api_key=None):
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    return client


class AIFS:
    def __init__(self, scenario: Scenario, data_manager: DataManager, api_key: Optional[str] = None, in_jupyter=False):
        self.client = get_client(api_key)
        self.assistant = self.client.beta.assistants.create(
            name="AIFS",
            instructions=get_scenario_instruction(scenario.value),
            model="gpt-4o",
        )
        self.thread = self.client.beta.threads.create()
        self.scenario = scenario
        self.data_manager = data_manager
        self.in_jupyter = in_jupyter
        self.last_image_path = None

    def submit_user_message(self, message):
        # Send Message to the Thread and Get Response
        self.client.beta.threads.messages.create(thread_id=self.thread.id, role="user", content=message)
        run = self.client.beta.threads.runs.create_and_poll(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )

        # Wait for the assistant to complete the response
        while not run.status == "completed":
            os.wait(0.1)
        return None

    def extract_last_message_content(self):
        # Display the assistant's response, simulating a response to Anna
        messages = self.client.beta.threads.messages.list(thread_id=self.thread.id)
        content = "\n".join([c.text.value for c in messages.data[0].content])
        content = content if content.startswith("AIFS: ") else "AIFS: " + content
        return content

    def chat(self):
        while True:
            # Capture user input
            user_input = input("Anna: ")  # Assuming input is always from Anna

            # Check for quit command
            if user_input.lower() == "q":
                print("Thank you so much for coming to the H&M store online. Have a great day! \nGoodbye!")
                break

            # Simulate sending a message from Anna
            anna_message = f"Anna: {user_input}"
            print(anna_message, "\n")

            if "taylor swift" in anna_message.lower() and self.last_image_path is not None:
                print("AIFS: One second, generating an image of Tylor Swift wearing the garment...")
                # generate an image of Tylor Swift wearing the garment
                image = generate_image(image_path=self.last_image_path, api_key=self.client.api_key)
                if self.in_jupyter:
                    display(image.resize((512, 512)))
                else:
                    image.show()
                continue

            self.submit_user_message(anna_message)
            content = self.extract_last_message_content()

            desired_garment_description = None
            if self.scenario in [Scenario.SCENARIO_1, Scenario.SCENARIO_2]:
                # extract the description of the desired garment from the response
                desired_garment_description = extract_from_square_brackets(content)
            else:
                # extract the description of the desired garment from the provided image
                image_link = extract_from_square_brackets(anna_message)
                if image_link is not None:
                    desired_garment_description = caption_image(image_url=image_link, api_key=self.client.api_key)
            # find the image of the article in the database that best matches the description
            if desired_garment_description is not None:
                # print the first part without the store request
                print("AIFS: Just a moment, looking for something exciting for you...")

                # find the image of the article in the database that best matches the description
                article_image_path = self.data_manager.get_image_path_from_text_query(desired_garment_description)
                # caption the article to insert its high quality description in the dialogue
                article_caption = caption_image(image_path=article_image_path, api_key=self.client.api_key)
                self.submit_user_message(f"The closest match in store is: [{article_caption}]")
                content = self.extract_last_message_content()

                # show the image of the article to Anna
                image = Image.open(article_image_path)
                if self.in_jupyter:
                    scale = 400 / max(image.size)
                    display(image.resize((int(image.width * scale), int(image.height * scale))))
                else:
                    image.show()
                self.last_image_path = article_image_path

            print(content, "\n")


def extract_from_square_brackets(response):
    # Extract the cloth description from the response
    cloth_description = response.split("[")
    if len(cloth_description) == 1:
        return None
    cloth_description = cloth_description[1].split("]")[0]
    return cloth_description
