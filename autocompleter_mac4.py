import copy
import typing as tp
import sys
from colorama import Fore, Back, Style
from sys import platform
from typing import List
import string

INITIAL_CURSOR_LINE = 4
INITIAL_CURSOR_COLUMN = 2
NUM_STORED_PRESSED_KEYS = 2
NUM_AUTOCOMPLETE_OPTIONS = 3
TERMINAL_WIDTH = 80

class State:

    def __init__(self):
        self.cursor_y: int = 4
        self.cursor_x: int = 1
        self.last_n_pressed_keys: list[str] = []
        # Example: ['I', 'SPACE', 'TAB', ...]
        self.completed_words: list[list[str]] = []
        # Example: [['I'], ['e', 'a', 't'], ['s', 'o', 'u', 'p']] -> "I eat soup"
        self.current_word: list[str] = []
        # Example: ['t', 'a', 'b', 'l', 'e']
        self.is_autocomplete_enabled: bool = False
        self.autocomplete_cursor_position: tp.Optional[int] = 0
        self.lines_end: list[int] = []

def draw_candidates(candidates, selected_candidate, y=None, x=None):
    width = max([len(i) for i in candidates] + [5])
    for i, candidate in enumerate(candidates):
        if selected_candidate == i:
            print_to_console(y+i, x, Fore.WHITE+Back.BLUE+f"{candidates[i]:^{width}}"+Style.RESET_ALL)
        else:
            print_to_console(y+i, x, Fore.WHITE+Back.BLACK+f"{candidates[i]:^{width}}"+Style.RESET_ALL)

def print_to_console(y, x, s):
    print("\033[{};{}H{}".format(y, x, s))

def move(y, x):
    print("\033[{};{}H".format(y, x))

def clean_window(y, x):
    for i in range(NUM_AUTOCOMPLETE_OPTIONS):
        move(y+i, x)
        print("\033[K")

def add_users_bigram(current_word, previous_word):
    pass

def get_pressed_key(platform):
    if platform == 'darwin':
        from getkey import getkey, keys
        key = getkey()
        if key == keys.SPACE:
            return "SPACE"
        if key == keys.UP:
            return "UP"
        if key == keys.DOWN:
            return "DOWN"
        if key == keys.ENTER:
            return "STOP"
        if key == keys.BACKSPACE:
            return "BACKSPACE"
        if key == keys.TAB:
            return "TAB"
        if key == keys.SPACE:
            return "SPACE"
        return key
    if system == "win32":
        import msvcrt
        key = msvcrt.getwch()
        if "à" in key: # стрелочки
            key = msvcrt.getwch()
        if key == "P":
            return "DOWN"
        elif key == "H":
            return "UP"
        if key.encode('utf-8') == b'\t': # tab
            return "TAB"
        if key.encode('utf-8') == b'\x03': # ctrl+c
            return "STOP"

        if key.encode('utf-8') == b'\r': # enter
            return "STOP"

        if key.encode('utf-8') == b'\x08': # backspace
            return "BACKSPACE"

        if key == " ":
            return "SPACE"

        return key



def split_to_tokens(text: str) -> List[str]:
    """
    Функция работает почти как метод str.split(), с некоторыми особенностями:
    - пустые строки не остаются в итоговом списке
    - знаки препинания в начале и в конце слова (все, кроме апострофа) отделяются от слова

    Example:
    split_to_tokens('John     said "Hey!" (and some other words.)') ->
    -> ['John', 'said', '"', 'Hey', '!', '"', '(', 'and', 'some', 'other', 'words', '.', ')']
    """
    words = text.split()
    new_words = []
    for word in words:
        new_word = ''
        symb_ind_b = 0
        symb_ind_e = len(word) - 1
        while symb_ind_b < len(word) and word[symb_ind_b] in PUNCTUATION:
            new_words.append(word[symb_ind_b])
            symb_ind_b += 1
        while word[symb_ind_e] in PUNCTUATION and symb_ind_e > -1:
            symb_ind_e -= 1
        for i in range(symb_ind_b, symb_ind_e + 1):
            new_word += word[i]
        new_words.append(new_word)
        for i in range(symb_ind_e + 1, len(word)):
            new_words.append(word[i])
    return new_words

def split_tokens_to_phrases(tokens: List[str], stoplist: List[str]) -> List[str]:
    """
    Функция получает на вход список токенов tokens и список разделителей stoplist,
    а возвращает список фраз.
    Фраза -- такой набор токенов, что
    - фраза содержит несколько токенов (>0), идущих в списке tokens подряд
    - фраза не содержит разделителей
    - перед фразой стоит разделитель из stoplist или начало списка tokens
    - после фразы стоит разделитель из stoplist или конец списка tokens

    Если простыми словами, нужно сложить слова в словосочетаниями,
    а границами этих словосочетаний являются элементы stoplist
    Example:
    split_tokens_to_phrases(
        tokens=["Mary", "and", "John", ",", "some", "words", "(", "and", "other", "words", ")"],
        stoplist=["and", ",", ".", "(", ")"]) ->
    -> ["Mary", "John", "some words", "other words"]
    """
    phrases = []
    phrase = []
    for word in tokens:
        if word.lower() in stoplist:
            if phrase:
                phrases.append(' '.join(phrase))
            phrase = []
        else:
            phrase.append(word)
    if phrase:
        phrases.append(' '.join(phrase))
    return phrases



PUNCTUATION = string.punctuation.replace("'", "") + "»" + "–" + "«" + "…" + "—"

def get_bigrams(txt_filename):
	f = open(txt_filename, 'r')
	t = f.read()
	phrases = split_tokens_to_phrases(split_to_tokens(t), PUNCTUATION)
	bigrams = [b for l in phrases for b in zip(l.split(" ")[:-1], l.split(" ")[1:])]
	dict_to_count = {}
	for bigram in bigrams:
		if bigram[0] not in dict_to_count.keys():
			dict_to_count[bigram[0]] = {}
		if bigram[1] not in dict_to_count[bigram[0]].keys():
			dict_to_count[bigram[0]][bigram[1]] = 0
		dict_to_count[bigram[0]][bigram[1]] += 1
	for word in dict_to_count:
		list_word = list(dict_to_count[word].items())
		list_word.sort(key=lambda i: i[1], reverse=True)
		dict_to_count[word] = list_word
	data = {}
	for word in dict_to_count:
		if len(dict_to_count[word]) <= 3:
			data[word] = dict_to_count[word]
		else:
			data[word] = dict_to_count[word][:3]
	return data

def main():
    state = State()
    bigrams = get_bigrams('kerroll-l.-alisa-v-strane-chudes-getlib.ru.txt')
    print("\033[2J")
    print_to_console(1, 1, "Чтобы прекратить работу программы, нажмите ENTER")
    move(state.cursor_y, state.cursor_x)
    platform = sys.platform
    while True:
        last_key = get_pressed_key(platform)
        state.last_n_pressed_keys.append(last_key)
        # существует очередь (queue.Queue), у которой быстро удаляется первый элемент и быстро добавляется последний
        if len(state.last_n_pressed_keys) > NUM_STORED_PRESSED_KEYS:
            state.last_n_pressed_keys.pop(0)
        previous_key = state.last_n_pressed_keys[0]
        if state.cursor_x >= TERMINAL_WIDTH:
            if state.current_word:
                print_to_console(state.cursor_y, state.cursor_x-len(state.current_word)+1, " "*len(state.current_word))
                print_to_console(state.cursor_y, state.cursor_x, "\n")
                state.lines_end.append(state.cursor_x)
                state.cursor_x = INITIAL_CURSOR_COLUMN
                state.cursor_y += 1
                print_to_console(state.cursor_y, state.cursor_x, ''.join(state.current_word))
                state.cursor_x += len(state.current_word) - 1
            else:
                print_to_console(state.cursor_y, state.cursor_x, "\n")
                state.lines_end.append(state.cursor_x)
                state.cursor_x = INITIAL_CURSOR_COLUMN
                state.cursor_y += 1
        if last_key == "STOP":
            break
        elif last_key == "DOWN":
            if state.is_autocomplete_enabled:
                state.autocomplete_cursor_position = (
                    (state.autocomplete_cursor_position + 1)
                    % NUM_AUTOCOMPLETE_OPTIONS)
                draw_candidates(candidates, 
                                state.autocomplete_cursor_position,
                                y=state.cursor_y+1,
                                x=state.cursor_x)
            else:
                pass
        elif last_key == "UP":
            if state.is_autocomplete_enabled:
                state.autocomplete_cursor_position = (
                    (state.autocomplete_cursor_position - 1)
                    % NUM_AUTOCOMPLETE_OPTIONS)
                draw_candidates(candidates,
                                state.autocomplete_cursor_position, 
                                y=state.cursor_y+1,
                                x=state.cursor_x)
            else:
                pass
        elif last_key == "SPACE":
            if state.current_word:
                # вот здесь...
                try:
                    candidates = [i[0] for i in bigrams[''.join(state.current_word)]]
                    state.is_autocomplete_enabled = True
                except KeyError:
                    candidates = []
                    pass
                state.completed_words.append(copy.deepcopy(state.current_word))
                state.current_word = []
                window_width = max([len(i) for i in candidates] + [5])
                if (state.cursor_x + window_width) >= TERMINAL_WIDTH:
                    print_to_console(state.cursor_y, state.cursor_x, "\n")
                    state.cursor_y += 1
                    state.lines_end.append(state.cursor_x)
                    state.cursor_x = 0
                    draw_candidates(candidates,
                                    state.autocomplete_cursor_position, 
                                    x=state.cursor_x, 
                                    y=state.cursor_y+1)
                else:
                     draw_candidates(candidates,
                                     state.autocomplete_cursor_position, 
                                     x=state.cursor_x+1, 
                                     y=state.cursor_y+1)
                # ...и вот здесь код для отрисовки
            else:
                state.completed_words.append([" "])
            state.cursor_x += 1
            print_to_console(state.cursor_y, state.cursor_x, " ")
                # просто добавить пробел
        elif last_key == "TAB":
            if previous_key in ["SPACE", "UP", "DOWN"] and state.is_autocomplete_enabled:
                # пишем выбранное слово
                state.is_autocomplete_enabled = False
                clean_window(state.cursor_y, state.cursor_x)
                state.cursor_x += 1
                state.current_word = list(candidates[state.autocomplete_cursor_position])
                print_to_console(state.cursor_y,
                                 state.cursor_x,
                                 candidates[state.autocomplete_cursor_position])
                state.cursor_x += len(state.current_word) - 1
                state.autocomplete_cursor_position = 0
                candidates = []
            else:
                pass
        elif last_key == "BACKSPACE":
            if state.is_autocomplete_enabled:
                clean_window(x=state.cursor_x, y=state.cursor_y)
                state.is_autocomplete_enabled = False
            if state.current_word:
                state.current_word = state.current_word[:-1]
                # отрисовка
            else:  # последний символ в тексте -- пробел
                state.current_word = state.completed_words[-1]
                state.completed_words.pop()
            print_to_console(state.cursor_y, state.cursor_x, " ")
            if state.cursor_x == INITIAL_CURSOR_COLUMN and state.cursor_y > INITIAL_CURSOR_LINE:
                state.cursor_x = state.lines_end[-1] + 2
                state.cursor_y -= 1
                state.lines_end.pop()
            else:  
                state.cursor_x -= 1
        else:
            if state.is_autocomplete_enabled:
                state.is_autocomplete_enabled = False
                clean_window(y=state.cursor_y, x=state.cursor_x)
            state.current_word.append(last_key.lower())
            state.cursor_x += 1
            print_to_console(state.cursor_y, state.cursor_x, last_key)
        clean_window(11, 2)
        clean_window(10, 2)
        print_to_console(10, 2, "позиция курсора: " + str(state.cursor_x))
        print_to_console(11, 2, "нажато " + last_key)
main()