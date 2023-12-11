# Анализ подписок пользователей на основе открытых данных выбранных заранее групп
## Основная информация 
Язык программирования: Python  
Получение данных с помощью: vk api  
Структурированное хранение и обработка: MySQL или SQLite3  
Взаимодействие пользователя с проектом: flet или PyTelegramBotApi (бот недоработан)
## Инсталляция библиотек
### Обязательно vk-api
```ruby
pip install vk-api
```
Указать в config.py токен аккаунта вконтакте
### Для работы с SQLite3
Ввести название базы данных в config.py  
инсталлировать ничего не нужно, он изначально есть в python
### Для работы с MySQL
```ruby
pip install mysql-connector-python
```
Отдельно на своей машине создать базу данных MySQL  
создать пользователя с доступом к базе  
внести данные в config.py  
(Если нет пароля, то оставить поле пустым)
### Для запуска приложения на flet
```ruby
pip install flet
```
```ruby
python on_sqlite3/app_main.py 
```
или
```ruby
python on_mysql/app_main.py 
```
### Для запуска telegram бота (не доработан)
```ruby
pip install PyTelegramBotApi
```
В bot_test_file.py на 7 строчке ввести токен бота  
перекинуть файл с ботом в папку on_mysql
```ruby
python on_mysql/bot_test_file.py
```
