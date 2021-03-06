from google.colab import drive
drive.mount('/content/drive', force_remount=False)

from keras_preprocessing.text import Tokenizer
from keras_preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
from sklearn.utils import compute_class_weight

import torch.utils.data as data_utils
import torch.functional as F
import torch.nn as nn
import torch
import numpy as np
import os, json, torch

if torch.cuda.is_available():
    device = 'cuda'
else:
    device = 'cpu'

torch.manual_seed(42)

# 1-layered LSTM with word embeddings
class LSTM(nn.Module):
    def __init__(self, embedding_dim, hidden_dim, vocab_size, output_size):
        super(LSTM, self).__init__()
        self.word_embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
        self.linear_1 = nn.Linear(hidden_dim, output_size*2)
        self.linear_2 = nn.Linear(output_size*2, output_size)
        self.tanh = nn.Tanh()
        self.softmax = nn.LogSoftmax(dim=-1)
        self.dropout = nn.Dropout()

    # forward pass --> receives tensor shape (batch_size, input_len)
    def forward(self, X):
        # TODO
        # implement forward pass using LSTM to output log probability of shape #(batch_size, output_size)
        # using self.softmax() at the end
        dummy_output = torch.ones(size=(X.shape[0], 8), requires_grad=True, device=device)  # this is a dummy output
        return dummy_output


# process Alexa data -> output X and Y
def process_data():
    path = '/content/drive/My Drive/Colab Notebooks/alexa_toy.json'
    # path = os.getcwd() + '/alexa_toy.json'

    with open(path) as f:
        data = json.load(f)

    # extract text and label
    text, label = [], []
    for k, v in data.items():
        for x in v['content']:
            text.append(x['message'].lower())
            label.append(x['sentiment'])

    # convert labels to index
    index, label_id = 0, {}
    for x in np.unique(label):
        label_id[x] = index
        index += 1
    label = [label_id[x] for x in label]

    # process text (for convenience, used keras tools)
    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(text)
    text = tokenizer.texts_to_sequences(text)
    text = pad_sequences(text, maxlen=50)

    train_x, test_x, train_y, test_y = train_test_split(text, label, test_size=0.05, shuffle=False, random_state=42)
    print ('training size : {} \t test size : {}'.format(len(train_y), len(test_y)))
    return train_x, test_x, train_y, test_y, tokenizer


# convert to dataloader class
def load_data(x, y):
    tensor_x = torch.tensor(x, device=device, dtype=torch.long)
    tensor_y = torch.tensor(y, device=device, dtype=torch.long)
    dataset = data_utils.TensorDataset(tensor_x, tensor_y)
    loader = data_utils.DataLoader(dataset=dataset, shuffle=True, batch_size=32)
    return loader


# compute accuracy
def compute_accuracy(pred, true):
    count = 0
    for x, y in zip(pred, true):
        if x == y:
            count += 1
    acc = count / len(true)
    return round(acc, 4)


# main training loop
def train():
    # load dataset
    train_x, test_x, train_y, test_y, tokenizer = process_data()
    train_loader = load_data(train_x, train_y)
    test_loader = load_data(test_x, test_y)
    vocab_size = len(tokenizer.word_index) + 1
    class_weights = compute_class_weight(class_weight='balanced', y=train_y, classes=np.unique(train_y))

    # init models
    model = LSTM(embedding_dim=50, hidden_dim=25, vocab_size=vocab_size, output_size=len(np.unique(train_y)))
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=5e-4)
    loss_func = nn.NLLLoss(weight=torch.tensor(class_weights, device=device, dtype=torch.float))

    for epoch in range(50):
        # train
        train_loss = 0.0
        for i, (x, y) in enumerate(train_loader):
            model.train()
            model.zero_grad()
            output = model(x)
            loss = loss_func(output, y)  #(batch_size, output_size) <--> (batch_size,)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

            if i % 100 == 0 and i != 0:
                # validate
                model.eval()
                preds, labels = [], []
                for j, (x, y) in enumerate(test_loader):
                    output = model(x)
                    output, y = output.detach().cpu().numpy(), y.detach().cpu().numpy()
                    output = np.argmax(output, axis=-1)
                    preds += list(output)
                    labels += list(y)
                acc = compute_accuracy(pred=preds, true=labels)
                print ('epoch: {} \t iter: {} \t train_loss: {} \t accuracy: {}'.format(epoch+1, i, round(train_loss/i, 3), acc))
            continue
    return


train()
