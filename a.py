from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("GAIR/rst-information-extraction-11b")
model = AutoModelForSeq2SeqLM.from_pretrained("GAIR/rst-information-extraction-11b")

with open("hack.txt", "r") as f:
    text = f.read()
inputs = tokenizer.encode(f"TEXT: {text} QUERY: When and where does the hackathon take place", return_tensors="pt")
outputs = model.generate(inputs)
print(tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=True))
pass