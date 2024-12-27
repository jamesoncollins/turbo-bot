import yfinance as yf
import matplotlib.pyplot as plt


def find_ticker(text):
  #pattern = r"\$[a-zA-Z]{3,4}"
  pattern = r"\$([a-zA-Z]{1,4})"
  matches = re.findall(pattern, text)
  return matches