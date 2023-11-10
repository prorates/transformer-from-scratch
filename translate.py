#!/usr/bin/env python3
from pathlib import Path
from tokenizers import Tokenizer
import torch
import sys

from dataset1 import get_testing_ds1, casual_mask, translation_mask
from dataset2 import get_testing_ds2
from dataset3 import get_testing_ds3

from config import get_model_folder, get_weights_file_path, get_config, latest_weights_file_path
from config import get_device
from config import EOS, SOS, PAD, UNK

from model1 import Transformer1, build_transformer1
from model2 import Transformer2, build_transformer2
from model3 import Transformer3, build_transformer3
from model4 import Transformer4, build_transformer4
from model5 import Transformer5, build_transformer5
from model6 import Transformer6, build_transformer6


def reload_model(config, model):
    preload = config['preload']
    model_filename = latest_weights_file_path(
        config) if preload == 'latest' else get_weights_file_path(config, preload) if preload else None
    print(f'Preloading model {model_filename}')
    if model_filename:
        state = torch.load(model_filename)
        model.load_state_dict(state['model_state_dict'])  # JEB: This was not in the video
    else:
        raise ValueError(f"{model_filename} Pretrained Model does not exist")
    return model


def build_model1(config: dict, vocab_src_len: int, vocab_tgt_len: int) -> Transformer1:
    model = build_transformer1(vocab_src_len, vocab_tgt_len, config['seq_len'], config['seq_len'],
                               d_model=config['d_model'], N=config['N'], h=config['h'], dropout=config['dropout'], d_ff=config['d_ff'])
    return model


def build_model2(config: dict, vocab_src_len: int, vocab_tgt_len: int) -> Transformer2:
    model = build_transformer2(vocab_src_len, vocab_tgt_len, config['seq_len'],
                               d_model=config['d_model'], N=config['N'], h=config['h'], dropout=config['dropout'], d_ff=config['d_ff'])
    return model


def build_model3(config: dict, vocab_src_len: int, vocab_tgt_len: int) -> Transformer3:
    model = build_transformer3(vocab_src_len, vocab_tgt_len, config['seq_len'], config['seq_len'],
                               d_model=config['d_model'], n_layers=config['N'], heads=config['h'], dropout=config['dropout'])
    return model


def build_model4(config: dict, vocab_src_len: int, vocab_tgt_len: int) -> Transformer4:
    model = build_transformer4(vocab_src_len, vocab_tgt_len, config['seq_len'], config['seq_len'],
                               d_model=config['d_model'], N=config['N'], h=config['h'], dropout=config['dropout'], d_ff=config['d_ff'])
    return model


def build_model5(config: dict, vocab_src_len: int, vocab_tgt_len: int) -> Transformer5:
    model = build_transformer5(vocab_src_len, vocab_tgt_len, config['seq_len'], config['seq_len'],
                               d_model=config['d_model'], N=config['N'], h=config['h'], dropout=config['dropout'], d_ff=config['d_ff'])
    return model


def build_model6(config: dict, vocab_src_len: int, vocab_tgt_len: int, src_to_index: dict, tgt_to_index: dict) -> Transformer6:
    model = build_transformer6(vocab_src_len, vocab_tgt_len, src_to_index, tgt_to_index, config['seq_len'], config['seq_len'],
                               d_model=config['d_model'], N=config['N'], h=config['h'], dropout=config['dropout'], d_ff=config['d_ff'])

    return model


def translate1(config: dict, sentence: str):
    device = get_device()

    model_folder = get_model_folder(config)
    if not Path.exists(Path(model_folder)):
        raise ValueError(f"{model_folder} model_folder does not exist")

    sentence, label, tokenizer_src, tokenizer_tgt = get_testing_ds1(config, model_folder, sentence)
    model = build_model1(config, tokenizer_src.get_vocab_size(), tokenizer_tgt.get_vocab_size()).to(device)

    # Load the pretrained weights
    model = reload_model(config, model)

    # if the sentence is a number use it as an index to the test set
    sos_token = torch.tensor([tokenizer_tgt.token_to_id(SOS)], dtype=torch.int64)
    eos_token = torch.tensor([tokenizer_tgt.token_to_id(EOS)], dtype=torch.int64)
    pad_token = torch.tensor([tokenizer_tgt.token_to_id(PAD)], dtype=torch.int64)

    model.eval()
    with torch.no_grad():
        # Precompute the encoder output and reuse it for every generation step
        # source = tokenizer_src.encode(sentence)
        # source = torch.cat([
        #     torch.tensor([tokenizer_src.token_to_id(SOS)], dtype=torch.int64),
        #     torch.tensor(source.ids, dtype=torch.int64),
        #     torch.tensor([tokenizer_src.token_to_id(EOS)], dtype=torch.int64),
        #     torch.tensor([tokenizer_src.token_to_id(PAD)] * (max_len - len(source.ids) - 2), dtype=torch.int64)
        # ], dim=0).to(device)
        enc_input_tokens = tokenizer_src.encode(sentence).ids
        enc_num_padding_tokens = config['seq_len'] - len(enc_input_tokens) - 2
        source = torch.cat(
            [
                sos_token,
                torch.tensor(enc_input_tokens, dtype=torch.int64),
                eos_token,
                torch.tensor([pad_token] * enc_num_padding_tokens, dtype=torch.int64),
            ],
            dim=0,
        ).to(device)
        source_mask = (source != pad_token.to(device)).unsqueeze(0).unsqueeze(0).int().to(device)
        # assert source.size(0) == 1, "Batch size must be 1 for validation"

        eos_idx = tokenizer_tgt.token_to_id(EOS)
        sos_idx = tokenizer_tgt.token_to_id(SOS)
        model_out = model.greedy_decode(source, source_mask, eos_idx, sos_idx, config['seq_len'], device)

    # Print the source sentence and target start prompt
    print(f"{f'Source: ':>15}{sentence}")
    if label != "":
        print(f"{f'Target: ':>15}{label}")
    print(f"{f'Prediction: ':>15}", end='')
    return tokenizer_tgt.decode(model_out)


def translate2(config: dict, sentence: str):
    device = get_device()

    model_folder = get_model_folder(config)
    if not Path.exists(Path(model_folder)):
        raise ValueError(f"{model_folder} model_folder does not exist")

    sentence, label, tokenizer_src, tokenizer_tgt = get_testing_ds2(config, model_folder, sentence)
    model = build_model2(config, tokenizer_src.get_vocab_size(), tokenizer_tgt.get_vocab_size()).to(device)

    # Load the pretrained weights
    model = reload_model(config, model)

    # if the sentence is a number use it as an index to the test set
    # run_translation(label, sentence, model, tokenizer_src, tokenizer_tgt, config['seq_len'], device)


def translate3(config: dict, sentence: str):
    device = get_device()

    model_folder = get_model_folder(config)
    if not Path.exists(Path(model_folder)):
        raise ValueError(f"{model_folder} model_folder does not exist")

    sentence, label, tokenizer_src, tokenizer_tgt = get_testing_ds3(config, model_folder, sentence)
    model = build_model3(config, tokenizer_src.get_vocab_size(), tokenizer_tgt.get_vocab_size()).to(device)

    # Load the pretrained weights
    model = reload_model(config, model)

    # if the sentence is a number use it as an index to the test set
    # run_translation(label, sentence, model, tokenizer_src, tokenizer_tgt, config['seq_len'], device)


def translate4(config: dict, sentence: str):
    device = get_device()

    model_folder = get_model_folder(config)
    if not Path.exists(Path(model_folder)):
        raise ValueError(f"{model_folder} model_folder does not exist")

    sentence, label, tokenizer_src, tokenizer_tgt = get_testing_ds4(config, model_folder, sentence)
    model = build_model3(config, tokenizer_src.get_vocab_size(), tokenizer_tgt.get_vocab_size()).to(device)

    # Load the pretrained weights
    model = reload_model(config, model)

    # if the sentence is a number use it as an index to the test set
    # run_translation(label, sentence, model, tokenizer_src, tokenizer_tgt, config['seq_len'], device)


def translate5(config: dict, sentence: str):
    device = get_device()

    model_folder = get_model_folder(config)
    if not Path.exists(Path(model_folder)):
        raise ValueError(f"{model_folder} model_folder does not exist")

    sentence, label, to5enizer_src, tokenizer_tgt = get_testing_ds5(config, model_folder, sentence)
    model = build_model5(config, tokenizer_src.get_vocab_size(), tokenizer_tgt.get_vocab_size()).to(device)

    # Load the pretrained weights
    model = reload_model(config, model)

    # if the sentence is a number use it as an index to the test set
    # run_translation(label, sentence, model, tokenizer_src, tokenizer_tgt, config['seq_len'], device)


def translate6(config: dict, sentence: str):
    device = get_device()

    model_folder = get_model_folder(config)
    if not Path.exists(Path(model_folder)):
        raise ValueError(f"{model_folder} model_folder does not exist")

    sentence, label, to5enizer_src, tokenizer_tgt = get_testing_ds6(config, model_folder, sentence)
    model = build_model6(config, tokenizer_src.get_vocab_size(), tokenizer_tgt.get_vocab_size()).to(device)

    # Load the pretrained weights
    model = reload_model(config, model)

    # if the sentence is a number use it as an index to the test set
    # run_translation(label, sentence, model, tokenizer_src, tokenizer_tgt, config['seq_len'], device)


if __name__ == '__main__':
    # warnings.filterwarnings('ignore')
    config = get_config()
    # read sentence from argument
    sentence = sys.argv[1] if len(sys.argv) > 1 else "I am not a very good a student."
    match config['alt_model']:
        case "model1":
            response = translate1(config, sentence)
        case "model2":
            reponse = translate2(config, sentence)
        case "model3":
            response = translate3(config, sentence)
        case "model4":
            response = translate4(config, sentence)
        case "model5":
            response = translate5(config, sentence)
        case "model6":
            response = translate6(config, sentence)
        case _:
            response = translate1(config, sentence)
