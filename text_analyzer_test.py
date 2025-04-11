import unittest
import os
import subprocess
import shutil


class TestTextAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Создаем временную директорию для тестов
        cls.test_dir = os.path.join(os.path.dirname(__file__), 'unittest')
        if not os.path.exists(cls.test_dir):
            os.makedirs(cls.test_dir)

        # Создаем тестовые файлы в поддиректориях
        cls.test_data = {
            '1': [("test1.txt", "Hello world! This is a test file.")],
            '2': [("test2.txt", "Another test file with words words words.")],
            '3': [("subdir/test3.txt", "File in subdirectory. Testing testing.")],
            '4': [
                ("file_a.txt", "Common words should be counted correctly."),
                ("file_b.txt", "Words words everywhere!")
            ],
            '5': [("special.txt", "Тестируем Unicode символы и русские слова. Тестируем.")],
            '6': [("empty.txt", "")],
            '7': [("large.txt", "Big " * 1000 + "file with many words.")]
        }

        for folder, files in cls.test_data.items():
            folder_path = os.path.join(cls.test_dir, folder)
            os.makedirs(folder_path, exist_ok=True)

            for filename, content in files:
                filepath = os.path.join(folder_path, filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

    @classmethod
    def tearDownClass(cls):
        # Удаляем тестовую директорию
        shutil.rmtree(cls.test_dir)

    def run_analyzer(self, directory, sort_by='path'):
        """Запускает утилиту и возвращает результат."""
        cmd = ['python', 'text_analyzer.py', directory, '--sort', sort_by]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr

    def test_single_file(self):
        """Тестируем обработку одного файла."""
        dir_path = os.path.join(self.test_dir, '1')
        stdout, stderr = self.run_analyzer(dir_path)

        self.assertIn("Самое часто встречающееся слово: 'a'", stdout)
        self.assertIn("test1.txt", stdout)
        self.assertEqual(stderr, "")

    def test_multiple_files(self):
        """Тестируем обработку нескольких файлов."""
        dir_path = os.path.join(self.test_dir, '4')
        stdout, stderr = self.run_analyzer(dir_path)

        self.assertIn("file_a.txt", stdout)
        self.assertIn("file_b.txt", stdout)
        self.assertIn("words", stdout.lower())
        self.assertEqual(stderr, "")

    def test_subdirectories(self):
        """Тестируем рекурсивный обход поддиректорий."""
        dir_path = os.path.join(self.test_dir, '3')
        stdout, stderr = self.run_analyzer(dir_path)

        self.assertIn("subdir\\test3.txt", stdout)
        self.assertIn("testing", stdout.lower())
        self.assertEqual(stderr, "")

    def test_unicode(self):
        """Тестируем обработку Unicode символов."""
        dir_path = os.path.join(self.test_dir, '5')
        stdout, stderr = self.run_analyzer(dir_path)

        self.assertIn("тестируем", stdout)
        self.assertEqual(stderr, "")

    def test_empty_file(self):
        """Тестируем обработку пустого файла."""
        dir_path = os.path.join(self.test_dir, '6')
        stdout, stderr = self.run_analyzer(dir_path)

        self.assertIn("Не удалось определить", stdout)
        self.assertEqual(stderr, "")

    def test_large_file(self):
        """Тестируем обработку большого файла."""
        dir_path = os.path.join(self.test_dir, '7')
        stdout, stderr = self.run_analyzer(dir_path)

        self.assertIn("large.txt", stdout)
        self.assertIn("1000", stdout)  # Проверяем что слово 'Big' встречается 1000 раз
        self.assertEqual(stderr, "")

    def test_sort_options(self):
        """Тестируем разные варианты сортировки."""
        dir_path = os.path.join(self.test_dir, '4')

        # Сортировка по пути
        stdout_path, _ = self.run_analyzer(dir_path, 'path')
        path_index_a = stdout_path.find("file_a.txt")
        path_index_b = stdout_path.find("file_b.txt")
        self.assertLess(path_index_a, path_index_b)

        # Сортировка по количеству (обратная)
        stdout_count, _ = self.run_analyzer(dir_path, '!count')
        count_index_a = stdout_count.find("file_a.txt")
        count_index_b = stdout_count.find("file_b.txt")
        self.assertLess(count_index_a, count_index_b)

    def test_invalid_directory(self):
        """Тестируем обработку несуществующей директории."""
        invalid_path = os.path.join(self.test_dir, 'nonexistent')
        _, stderr = self.run_analyzer(invalid_path)

        self.assertIn("не является директорией", stderr)

    def test_word_count(self):
        dir_path = os.path.join(self.test_dir, '2')
        stdout, _ = self.run_analyzer(dir_path)
        self.assertIn("'words' встречается: 3", stdout)


if __name__ == '__main__':
    unittest.main()