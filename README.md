<img src="./imgs/vkquick-header.jpg" alt="VK Quick шапка" align="center">

*__VK Quick__* — __это современный асинхронный фреймворк для создания ботов ВКонтакте, автоматически генерирующий документацию к командам бота в виде сайта__

* [__Официальное сообщество в ВКонтакте__](https://vk.com/vkquick)

* [__Официальная беседа, где отвят на любой вопрос по API и разработке ботов__](https://vk.me/join/AJQ1dzLqwBeU7O0H_oJZYNjD)

* [__Официальный сайт с документацией__](https://vkquick.rtfd.io)

***

## Ключевые особенности:

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/vkquick)
[![Downloads](https://pepy.tech/badge/vkquick)](https://pepy.tech/project/vkquick)

* __Скорость__: VK Quick использует конкурентность в одном потоке (asyncio) и является одним из самых быстрых фреймворков для разработки ботов

* __Компактность кода__: Разработка требует меньше времени в несколько раз, код становится короче, вероятность возникновения багов уменьшается. VK Quick _автоматически_ создает документацию к написанному боту, позволяя сконцентрироваться разработчику именно на самом коде

* __Легкое обучение__: Создавать ботов невероятно просто вместе с VK Quick! Обучение проходит быстро и легко

* __Инструменты для упрощения разработки__: Из коробки VK Quick представляет CLI (терминальная утилита) — инструмент, облегающий процесс создания команд, настройки проекта и выстраивания архитектуры

* __Поддержка актуального API__: Множество разных возможностей для ботов перенесены в удобный Python-стиль, любые нововведения в социальной сети незамедлительно отображаются в самом фреймворке

* __Отзывчивое коммьюнити__: Вы всегда можете обратиться с вопросом, на который обязательно ответят наши специалисты по разработке ботов в официальной беседе нашего сообщества

***

## Установка
```shell script
python -m pip install vkquick
```
> До релиза 1.0: `python -m pip install https://github.com/deknowny/vkquick/archive/master.zip`


Вместе с фреймворком устанавливается треминальная утилита — `kwik`:

```shell script
kwik --help
```
***

# Echo-бот
Прежде чем создать своего первого бота, нужно получить специальный __токен__ — ключ, через который можно взаимодействовать с ресурсами ВК. VK Quick позволяет писать ботов как для групп, так и пользователей в одном стиле — достаточно запустить код с нужным токеном.


```python
import vkquick as vq


app = vq.App(debug=False)


@app.command("пинг", "ping")
async def greeting():
    """
    Самая обычная пинг-понг команда
    """
    return "Понг!"


@app.command("дата", prefixes=["/"])
async def resolve_user(user: vq.User):
    """
    Возвращает дату регистрации указанного пользователя
    """
    registration_date = await vq.get_user_registration_date(user.id)
    formatted_date = registration_date.strftime("%d.%m.%Y")
    return f"Дата регистрации пользователя {user:@[fullname]}: {formatted_date}"


app.run("token")
```

Остается подставить вместо `"token"` свой токен. Теперь у нас есть бот сразу с двумя командами!

<img src="./imgs/echo-example.png" alt="Пример работы бота" style="padding: 10%">


И __автоматически__ созданная документация по командам в папке `autodocs`

<img src="./imgs/autodocs-example.png" alt="Пример автоматически сгенерированной документации" style="padding: 10%">

Хотите больше возможностей? Переходите на наш официальный сайт [https://vkquick.rtfd.io](https://vkquick.rtfd.io) и продолжайте углубляться в разработку ботов вместе с VK Quick!
