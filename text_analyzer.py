import argparse
import chardet
import os
import sys
from collections import defaultdict
from unicodedata import category


def get_text_files(directory):
    """Рекурсивно получаем все текстовые файлы в директории и поддиректориях."""
    text_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                text_files.append(os.path.join(root, file))
    if not text_files:
        print(f"Предупреждение: в директории {directory} не найдено .txt файлов.")
    return text_files


def count_chars_and_words(file_path):
    """Считаем символы и слова в файле, возвращаем статистику."""
    # Определяем кодировку файла
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # Читаем первые 10КБ для определения кодировки
            encoding = chardet.detect(raw_data)['encoding']

            if encoding is None:
                encoding = 'utf-8'
    except Exception as e:
        raise AttributeError(f'Ошибка чтения файла {file_path}: {e}')

    char_counts = defaultdict(int)
    word_counts = defaultdict(int)
    total_chars = 0
    current_word = []

    with open(file_path, 'r', encoding=encoding, errors='replace') as f:
        for line in f:
            for char in line:
                total_chars += 1
                char_counts[char] += 1

                if category(char)[0] == 'L':
                    current_word.append(char)
                elif current_word:
                    word_counts[''.join(current_word).casefold()] += 1
                    current_word = []

    if current_word:
        word_counts[''.join(current_word).casefold()] += 1
    total_words = sum(word_counts.values())

    return char_counts, word_counts, total_chars, total_words


def process_files(directory):
    """Обрабатываем все файлы и собираем общую статистику."""
    files = get_text_files(directory)

    total_char_counts = defaultdict(int)
    total_word_counts = defaultdict(int)
    file_stats = {}

    for file_path in files:
        char_counts, word_counts, total_chars, total_words = count_chars_and_words(file_path)
        file_stats[file_path] = {
            'char_counts': char_counts,
            'word_counts': word_counts,
            'total_chars': total_chars,
            'total_words': total_words
        }

        # Обновляем общие счетчики символов и слов
        for char, count in char_counts.items():
            total_char_counts[char] += count

        for word, count in word_counts.items():
            total_word_counts[word] += count

    return total_char_counts, total_word_counts, file_stats


def get_most_common(items):
    """Возвращает самый часто встречающийся элемент и его количество."""
    if not items:
        return None, 0
    try:
        """Если найдено несколько элементов с одинаковой частотой, и она максимальная, 
        то возвращается первый элемент в лексикографическом порядке."""
        most_common_tmp = max(items.items(), key=lambda x: x[1])
        most_common_list = [pair for pair in items.items() if pair[1] == most_common_tmp[1]]
        most_common_list.sort()
        most_common = most_common_list[0]
        return most_common
    except Exception as e:
        raise AttributeError(f"Ошибка при определении наиболее частого элемента: {e}")


def get_file_list_with_counts(file_stats, count_key, target):
    """Создаем список файлов, содержащих целевой символ/слово с их статистикой."""
    file_list = []

    # Определяем соответствующий ключ для общего количества
    total_key = {
        'char_counts': 'total_chars',
        'word_counts': 'total_words'
    }.get(count_key)

    if total_key is None:
        raise ValueError(f"Неизвестный ключ счётчика: {count_key}. "
                         f"Ожидается 'char_counts' или 'word_counts'")

    for file_path, stats in file_stats.items():
        counts_dict = stats.get(count_key, {})
        count = counts_dict.get(target, 0) if target is not None else 0

        if count > 0:
            file_list.append({
                'file_path': file_path,
                'total': stats.get(total_key, 0),
                'count': count
            })

    return file_list


def sort_file_list(file_list, sort_by):
    """Сортируем список файлов по указанному критерию."""
    if not file_list:
        return file_list

    reverse = False
    if sort_by.startswith('!'):
        reverse = True
        sort_by = sort_by[1:]

    try:
        if sort_by == 'path':
            key = lambda x: x['file_path']
        elif sort_by == 'total':
            key = lambda x: x['total']
        elif sort_by == 'count':
            key = lambda x: x['count']
        else:
            raise ValueError(f"Неизвестный критерий сортировки: {sort_by}")

        return sorted(file_list, key=key, reverse=reverse)
    except Exception as e:
        print(f"Ошибка сортировки: {e}. Используется сортировка по пути.", file=sys.stderr)
        return sorted(file_list, key=lambda x: x['file_path'])


def print_results(most_common_char, char_files, most_common_word, word_files):
    """Выводим результаты в консоль."""
    if most_common_char[0] is not None:
        print(f"Самый часто встречающийся символ: '{most_common_char[0]}' (встречается {most_common_char[1]} раз)")
        print("\nФайлы, содержащие этот символ:")
        for file in char_files:
            print(
                f"  {file['file_path']} - всего символов: {file['total']}, '{most_common_char[0]}' встречается: {
                file['count']}")
    else:
        print("Не удалось определить самый частый символ.")

    if most_common_word[0] is not None:
        print(f"\nСамое часто встречающееся слово: '{most_common_word[0]}' (встречается {most_common_word[1]} раз)")
        print("\nФайлы, содержащие это слово:")
        for file in word_files:
            print(
                f"  {file['file_path']} - всего слов: {file['total']}, '{most_common_word[0]}' встречается: {
                file['count']}")
    else:
        print("\nНе удалось определить самое часто встречающееся слово.")


def main():
    parser = argparse.ArgumentParser(description='Анализирует текстовые файлы на предмет самых частых символов и слов.')
    parser.add_argument('directory', help='Путь к директории с текстовыми файлами')
    parser.add_argument('--sort',
                        default='path',
                        choices=['path', '!path', 'total', '!total', 'count', '!count'],
                        help='Критерий сортировки файлов (path, total, count, !path, !total, !count)')

    args = parser.parse_args()

    try:
        if not os.path.isdir(args.directory):
            raise Exception(f"{args.directory} не является директорией.")

        total_char_counts, total_word_counts, file_stats = process_files(args.directory)
    except AttributeError as ae:
        print(ae)
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при поиске файлов: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if not file_stats:
            print("Нет данных для анализа. Возможно, в указанной директории нет .txt файлов.", file=sys.stderr)
            sys.exit(0)

        most_common_char = get_most_common(total_char_counts)
        most_common_word = get_most_common(total_word_counts)

        char_files = get_file_list_with_counts(file_stats, 'char_counts', most_common_char[0])
        word_files = get_file_list_with_counts(file_stats, 'word_counts',
                                               most_common_word[0].lower() if most_common_word[0] else None)

        char_files_sorted = sort_file_list(char_files, args.sort)
        word_files_sorted = sort_file_list(word_files, args.sort)

        print_results(most_common_char, char_files_sorted, most_common_word, word_files_sorted)
    except AttributeError as ae:
        print(ae)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nРабота программы прервана пользователем.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Критическая ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
