import tiktoken 

# Tokenization - Encoding Text
# Convert text into tokens using a specific encoding
# This is the process of turning text into a sequence of numbers that represent the characters in the text

encoding = tiktoken.encoding_for_model("gpt-4o")

text = "Hey There! My name is John Doe."
# Tokens  [25216, 3274, 0, 3673, 1308, 382, 5928, 78200, 13]

tokens = encoding.encode(text)
print("Encoded Tokens: ", tokens)

#Decoding Text
# Convert tokens back into text using the same encoding
# This is the process of turning a sequence of numbers back into text

decoded_text = encoding.decode(tokens)
print("Decoded Text ", decoded_text)
