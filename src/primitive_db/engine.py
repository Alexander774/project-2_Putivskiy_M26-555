import prompt


def welcome() -> None:
    print("Первая попытка запустить проект!")
    print("***")

    help_text = (
        "<command> exit - выйти из программы\n"
        "<command> help - справочная информация"
    )

    print(help_text)

    while True:
        command = prompt.string(prompt="Введите команду: ").strip()

        if command == "exit":
            break
        elif command == "help":
            print(help_text)
        else:
            print(f"Неизвестная команда: {command}")