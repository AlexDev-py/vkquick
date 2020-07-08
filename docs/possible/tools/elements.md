Элементы — составляющая карусели. Иницициализация происходит 2мя способами

1. Через метод `by`, который принимает словарь, описывающий схему элемента карусели (точно также как предыдущие)
2. Через инициализацию, передавая соответсвющие поля:
    * `buttons`: Список кнопок
    * `title`: Заголовок элемента
    * `description`: Описание элемента
    * `photo_id`: ID владельца и ID самой фотографии, соединенные `_`

После чего нужно обозначить действие, которое должно происходить по нажатию на элемент: открытие сайта, либо открытие фотографии элемента

* `vq.Element(......).open_link("https://google.com")`
* `vq.Element(......).open_photo()`

Содержимая схема в виде словаря находится в поле `info`