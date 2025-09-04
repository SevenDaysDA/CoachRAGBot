from ragchatbot import RAGChatbot
import json
import time
import csv

# Load your labeled dataset
with open("manager_dataset.json", "r") as f:
    dataset = json.load(f)

# Initialize the chatbot
chatbot = RAGChatbot()

# Prepare CSV for failed examples
csv_file = "failed_queries.csv"
with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "question", "expected", "response"])

correct = 0
start_time = time.time()
length_dataset = 0

for idx, entry in enumerate(dataset):
    question = entry["question"]
    expected = entry["managerLabel"]
    question_type = entry["type"]
    used_model = "vanilla_gazetteer"

    if question_type == "spelling_error":
        length_dataset += 1

        response = chatbot.process_query(question).get("context").get("manager_name")

        if not response:  # handle empty response
            response = ""

        # Compare (case-insensitive)
        if expected.lower() in response.lower():
            correct += 1
        else:
            # Save failed query to CSV
            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([idx, question, expected, response, question_type, used_model])

end_time = time.time()

accuracy = correct / length_dataset * 100
elapsed = end_time - start_time

print(f"Total queries: {length_dataset}")
print(f"Correct responses: {correct}")
print(f"Accuracy: {accuracy:.2f}%")
print(f"Total time: {elapsed:.2f} seconds")
print(f"Average time per query: {elapsed/length_dataset:.3f} seconds")
print(f"Failed queries saved in {csv_file}")
