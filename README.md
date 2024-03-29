## Yatube
***
### Описание:
Yatube - сервис позволяющий Вам создавать и просматривать публикации.
С его помощью вы легко загрузите на сайт любимое фото, поделитесь своими мыслями.
Вы можете подписаться на друга или интересного автора, а также оставить комментарий под его публикацией.
***
### Технологии:
Бэкенд представляет собой приложение написанное на python 3.9 с использованием фреймфорка Django 2.2.
Фронтенд представляет собой страницы написанные на html с подключением css стилей. 
Также подключена база данных SQLite, используется кэширование данных, настроена пагинация статей на странице.
***
### Как запустить проект:

#### 1. Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/Aleksandr27041986/Yatube.git
```

```bash
cd Yatube
```

#### 2. Запуск проекта на локальном сервере:

Cоздать и активировать виртуальное окружение:
```bash
python3 -m venv env
```
* Если у вас Linux/macOS
    ```bash
    source env/bin/activate
    ```
* Если у вас windows
   ```bash
    source env/scripts/activate
    ```
```bash
python3 -m pip install --upgrade pip
```
Установить зависимости из файла requirements.txt:
```bash
pip install -r requirements.txt
```
Выполнить миграции:
```bash
python3 manage.py migrate
```
Запустить проект:
```bash
python3 manage.py runserver
```

#### Авторы проекта:
Автором является начинающий программист, обучающийся на курсе [Yandex Practicum](https://practicum.yandex.ru/)
Шестаков Александр - [github](https://github.com/Aleksandr27041986), [telegram](https://t.me/Sanila270486)
