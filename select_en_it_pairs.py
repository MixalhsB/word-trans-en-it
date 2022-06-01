from googletrans import Translator
from os import path
import subprocess
import random


def select_server(l):
    return random.choice(l)


def translate_text(text, list_of_servers, src_language='it', dest_language='en'):
    translator = Translator()
    try:
        translation = translator.translate(text=text, dest=dest_language)
    except:
        print('exception! deconnecting from VPN')
        process = subprocess.Popen(['nordvpn', '-d'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        time.sleep(5)
        srv = select_server(list_of_servers)
        print('selecting VPN server "'+ srv + '" and connecting')
        process = subprocess.Popen(['nordvpn', '-c', '-g', srv], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.wait()
        time.sleep(10)
        return translate_text(text=text, dest_language=dest_language)
    return translation.text


def main():
    words_it_original_w2v = {}
    print('Loading in IT-WIKI words, just top 1000.')
    with open('data/itwiki-20171103-pages-articles.w2v.top1000.txt', 'r', encoding='utf-8') as f:
        for line in f:
            word, vector_string = line.split(' ', 1)
            vector_list = vector_string.split()
            words_it_original_w2v[word] = ' '.join([str(round(float(x), 4)).ljust(7 if float(x) < 0 else 6, '0') for x in vector_list]) + '\n'
    
    if not path.exists('data/itwiki-translated-to-english.txt'):
        list_of_servers = ['South Africa', 'Egypt' , 'Australia', 'New Zealand',  'South Korea', 'Singapore', 'Taiwan', 'Vietnam',
                           'Hong Kong', 'Indonesia', 'Thailand', 'Japan', 'Malaysia', 'United Kingdom', 'Netherlands', 'Germany',
                           'France', 'Belgium', 'Switzerland', 'Sweden','Spain','Denmark', 'Italy', 'Norway', 'Austria', 'Romania',
                           'Czech Republic', 'Luxembourg', 'Poland', 'Finland', 'Hungary', 'Latvia', 'Russia', 'Iceland', 'Bulgaria',
                           'Croatia', 'Moldova', 'Portugal', 'Albania', 'Ireland', 'Slovakia', 'Ukraine', 'Cyprus', 'Estonia', 'Georgia',
                           'Greece', 'Serbia', 'Slovenia', 'Azerbaijan', 'Bosnia and Herzegovina', 'Macedonia', 'India', 'Turkey',
                           'Israel', 'United Arab Emirates', 'United States', 'Canada', 'Mexico', 'Brazil', 'Costa Rica', 'Argentina',
                           'Chile']
        words_en_translated = []    
        for i, word in enumerate(words_it_original_w2v):
            try:
                tl_out = translate_text(word, list_of_servers, src_language='it', dest_language='en')
                words_en_translated.append(tl_out)
                print(str(i) + ':\t', word, '->', tl_out)
            except Exception as e:
                print(str(e))
                words_en_translated.append(None)
        with open('data/itwiki-translated-to-english.txt', 'w', encoding='utf-8') as f:
            for word in words_en_translated:
                f.write(word + '\n')
    else:
        with open('data/itwiki-translated-to-english.txt', 'r', encoding='utf-8') as f:
            words_en_translated = [x for x in f.read().split('\n') if x]
    
    unique_pairs = []
    if not path.exists('data/pairs_en_it.txt'):
        print('Loading in EN-WIKI words ... (might take a while)')
        words_en_all = {}
        with open('data/enwiki_20180420_300d.txt', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                word, vector_string = line.split(' ', 1)
                words_en_all[word] = i
        raw_pairs = []
        en_word_counts = {}
        for en_word, it_word in zip(words_en_translated, words_it_original_w2v):
            if en_word in words_en_all and en_word != it_word:
                raw_pairs.append((en_word, it_word))
                if en_word not in en_word_counts:
                    en_word_counts[en_word] = 1
                else:
                    en_word_counts[en_word] += 1
        
        manually_selected_bad_pairs = [('are', 'su'), ('with', 'se'), ('lap', 'volta'), ('who', 'qui'), ('not', 'ora'),
                                       ('party', 'parti'), ('cottage', 'prese'), ('thousand', 'mano'), ('set', 'sette'),
                                       ('decisive', 'decise'), ('almost', 'casi'), ('see', 'sé'), ('discovery', 'scoperto'),
                                       ('rarely', 'reti'), ('step', 'passò'), ('port', 'portò'), ('within', 'entrò')]
        
        for en_word, it_word in raw_pairs:
            if en_word_counts[en_word] == 1:
                if (en_word, it_word) not in manually_selected_bad_pairs:
                    unique_pairs.append((en_word, it_word))
        
        with open('data/pairs_en_it.txt', 'w', encoding='utf-8') as f:
            for en_word, it_word in unique_pairs:
                assert ' ' not in en_word and ' ' not in it_word
                f.write(en_word + ' ' + it_word + '\n')
        
        words_en_matched_w2v = {}
        en_words_in_unique_pairs = [en_word for en_word, it_word in unique_pairs]
        with open('data/enwiki_20180420_300d.txt', 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                word, vector_string = line.split(' ', 1)
                if words_en_all[word] == i and word in en_words_in_unique_pairs:
                    words_en_matched_w2v[word] = vector_string
        
        with open('data/english.subset.388.dm', 'w', encoding='utf-8') as f:
            for word_en, _ in unique_pairs:
                f.write(word_en + ' ' + words_en_matched_w2v[word_en])
        
        with open('data/italian.subset.388.dm', 'w', encoding='utf-8') as f:
            for _, word_it in unique_pairs:
                f.write(word_it + ' ' + words_it_original_w2v[word_it])
        
    else:
        with open('data/pairs_en_it.txt', 'r', encoding='utf-8') as f:
            for line in f:
                en_word, it_word = line.rstrip('\n').split(' ')
                unique_pairs.append((en_word, it_word))
        assert path.exists('data/english.subset.388.dm')
        assert path.exists('data/italian.subset.388.dm')
    
    return unique_pairs


if __name__ == '__main__':
    unique_pairs = main()
