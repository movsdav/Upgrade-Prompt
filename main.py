import json
import csv
from ollama import Client

client = Client(host='http://192.168.1.88:11434')
# client = Client(host='http://localhost:11434')

prompt_new_2 = """Your task is to analyze restaurant reviews and extract relevant facts for specific predefined categories. Follow the instructions exactly as described below.

### Key Objectives:
1. **Fact Extraction**: Extract relevant facts directly from the review, ensuring they are copied exactly as they appear (verbatim).
2. **Sentiment and Intensity**: For each extracted fact, assign a sentiment score (1 for positive, -1 for negative) and an intensity score (on a scale from 1 to 5).

### Categories to Analyze:
- Place Accessibility
- Place Availability
- Activity Level
- Atmosphere & Comfort
- Customization Options
- General Sentiment
- Hygiene & Compliance
- Price & Fairness
- Product Quality
- Restrictions
- Safety & Trust
- Service Quality
- Specialization/Customer Need or Interest
- Target Audience
- Timing
- Uniqueness
- Consistency

### Response Format:
Your response must be in the following JSON structure:
"
"Category_Name": { "sntm": 1 or -1, "score": 1 to 5, "eF": "Exact extracted fact" }"
"
- **Category_Name**: Replace with the relevant category name from the list above. Do not modify or underscore the category names.
- **sntm**: Assign a sentiment score, either 1 for positive or -1 for negative.
- **score**: Assign an intensity score on a scale from 1 to 5.
- **eF**: Extract the exact fact from the review verbatim.

### Guidelines:
1. **Inclusion**: Include only those categories where relevant facts are found in the review.
2. **Omission**: Omit any categories that are not mentioned or where no relevant facts are found. Do not include placeholders, empty categories, or any categories without relevant extracted facts.
3. **Verbatim Facts**: Extract facts exactly as they appear in the review without paraphrasing or altering them.
4. **No Example Values**: Do not use the example values given below in your response.

### Important Note: 
The category names, sentiment scores, intensity scores, and extracted facts must be exactly as instructed. Categories without relevant facts must be omitted.

### Example:
Review Text:
" The food was overcooked and tasteless. The restaurant was too hot, and the staff was rude. "

Expected Output:
"
"Product Quality": { "sntm": -1, "score": 5, "eF": "The food was overcooked and tasteless." },
"Atmosphere & Comfort": { "sntm": -1, "score": 4, "eF": "The restaurant was too hot." },
"Service Quality": { "sntm": -1, "score": 3, "eF": "The staff was rude." }
"

### Review to Analyze:
"
{{review}}
"
"""

ALL_CATEGORIES = [
    "Place Availability",
    "ActivityLevel",
    "Atmosphere & Comfort",
    "Customization Options",
    "General Sentiment",
    "Hygiene & Compliance",
    "Price & Fairness",
    "Product Quality",
    "Restrictions",
    "Safety & Trust",
    "Service Quality",
    "Specialization/Customer Need or Interest",
    "Target Audience",
    "Timing",
    "Uniqueness",
    "Consistency"
]

def run_models(models, review, model_responses_store: list = []):
    result = []

    prompt = prompt_new_2.replace("{{review}}", review)

    for model in models:
        model_result = {
            model: {}
        }
        print(f"===================== Start of model {model} =====================")
        for run_number in range(3):
            response = client.generate(model=model, prompt=prompt, format='json')
            print(response)
            total_duration = response.get('total_duration')

            time_in_sec = (int(total_duration / 1000000000)) if total_duration else "NO TIME PROVIDED WITH RESPONSE"
            if time_in_sec == "NO TIME PROVIDED WITH RESPONSE":
                print("Response was invalid (omitted total_duration). Retrying one more time.")
                response = client.generate(model=model, prompt=prompt, format='json')
                total_duration = response.get('total_duration')
                if not total_duration:
                    print("Unable to retrieve valid response. Skipping this run")
                    continue
                time_in_sec = (int(total_duration / 1000000000))

            response = json.loads(response['response'])
            print(f'{run_number}. Response for {model} is ready. it took {time_in_sec} sec')
            response_data = {
                'model_name': model,
                'comment': review,
                'response': response
            }
            model_responses_store.append(json.dumps(response_data))
            print(response_data)
            print('-------------------------------------------------------------------------------')

            model_result[model][time_in_sec] = response

        print(f"======================== End of model {model} ==========================")
        result.append(model_result)
    return result

def get_most_fast_model_response(*model_responses):
    result = []
    for model_response in model_responses:
        model_name = list(model_response.keys())[0]
        model_work_times = model_response[model_name].keys()
        min_time = min(model_work_times)
        result.append(
            {"model_name": model_name, "time_in_seconds": min_time, "json_data": model_response[model_name][min_time]})

    return result

def process_json(models, all_categories=ALL_CATEGORIES):
    result = [["Model", "Time In Seconds", *ALL_CATEGORIES]]
    for model in models:
        json_data = model['json_data']
        model_name = model['model_name']
        time_in_seconds = model['time_in_seconds']
        # Prepare the data row
        data_row = [model_name, time_in_seconds]

        for category in all_categories:
            category_data = json_data.get(category, {})
            score = 0
            intensity = 0
            extracted_facts = ""
            if category_data and isinstance(category_data, dict):
                score = category_data.get("score", "")
                intensity = category_data.get("sntm", "")
                extracted_facts = category_data.get("eF", "")

            # If any of the fields are missing or invalid, we'll insert a blank
            if score == 0 or intensity == 0 or extracted_facts == "":
                data_row.append("No extracted fact for this category or data was in wrong format.")
            else:
                data_row.append(f"Sent: {score},\nScore: {intensity},\nFact: {extracted_facts}")

        result.append(data_row)
    return result

comment = """Bread was stale. Dead bug on the menu. We ordered two skirt steaks and they were super chewy, overdone and not seasoned. The Branzino had no flavor. Food was just no good. The place was so hot and they didn’t have the AC on."""
# comment = """Hands down one of the worst dining experiences I’ve had. The pasta was completely undercooked and tasted terrible. The bread was cold and stale, and the service was non-existent. They also charged us a 20% gratuity without even telling us, which felt like a total scam. I honestly don't understand how this place has good reviews—I was extremely disappointed and won’t be returning."""

models = ['llama3.2', 'llama3.2:3b-text-q8_0', 'qwen2.5:0.5b', 'qwen2.5:1.5b', 'qwen2.5:3b', 'qwen2.5:7b',
          'qwen2.5:14b']

# current_prompt = prompt_new_2.replace("{{review}}", comment)

how_many_time_to_repeat = 3

with open('mixed_reviews_array.json', 'r') as f:
    reviews = json.load(f).get('data')

# for review in reviews:
#     store = []
#     run_models(models, review, store)
#     with open("results.txt", "a") as f:
#         f.write(f"{'\n'.join(store)}\n")


result = run_models(models, comment)

most_fast_results = get_most_fast_model_response(*result)

data_for_csv = process_json(most_fast_results)

data_for_csv.append([])
data_for_csv.append(['Review: ', comment])

with open('result.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data_for_csv)
