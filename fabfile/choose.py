from output import notify
from fabric.api import abort
from fabric.colors import blue, cyan, green, red, white
from fabric.utils import fastprint


def choose(msg, options):
    choices = range(len(options))

    fastprint(white(msg, bold=True) + white("\n"))
    for i, target in enumerate(options):
        fastprint("{0}. {1}\n".format(i, target))
    fastprint("x. Cancel\n")

    user_input = raw_input("> ")
    if user_input == 'x':
        abort("Cancelled")

    try:
        choice = int(user_input)
    except:
        fastprint(red("Choice must be an integer"))
        return None

    if choice not in choices:
        fastprint(red("Choice must be one of {0}".format(choices)))
        return None

    return options[choice]


def multi_choose_with_input(msg, options):
    """
    Options:
        msg - header message for the chooser
        options - dictionary of options to select


    User selects one of the keys in the dictionary,
    a new value is read from stdin
    """

    selections = options.keys()
    user_input = None

    while True:
        fastprint('\n{0}{1}'.format(white(msg, bold=True), white("\n")))

        # The extra white("\n") prints are to reset
        # the color for the timestamp line prefix

        fastprint(white("\n"))
        for i, item in enumerate(selections):
            fastprint(" {0}. {1} : {2}".format(white(i, bold=True),
                cyan(item), cyan(options[item], bold=True)) + white("\n"))
        fastprint(blue("  a. Select all") + white("\n"))
        fastprint(blue("  c. Continue") + white("\n"))
        fastprint(blue("  x. Cancel") + white("\n"))
        fastprint(white("\n"))
        user_input = raw_input("> ")

        try:
            if user_input == 'c':
                break
            elif user_input == 'x':
                return None
            elif int(user_input) in range(len(selections)):
                name = selections[int(user_input)]
                fastprint(green('Enter new msg for ') +
                        cyan(name))
                options[name] = raw_input(white(": "))
        except:
            notify("Invalid selection ->" + user_input + "<-")
    return options


def multi_choose(msg, options):

    fastprint(white(msg, bold=True) + white("\n"))
    selected = [" " for option in options]

    user_input = None

    while True:

        # The extra white("\n") prints are to reset
        # the color for the timestamp line prefix

        fastprint(white("\n"))
        for i, target in enumerate(options):
            fastprint(green(selected[i]))
            fastprint(cyan(" {0}. {1}".format(i, target)) + white("\n"))
        fastprint(blue("  a. Select all") + white("\n"))
        fastprint(blue("  c. Deploy selections") + white("\n"))
        fastprint(blue("  x. Cancel") + white("\n"))
        fastprint(white("\n"))

        user_input = raw_input("> ")

        try:
            if user_input == 'c':
                break
            elif user_input == 'a':
                selected = ['*' for i in range(len(selected))]
            elif user_input == 'x':
                return None
            elif int(user_input) in range(len(options)):
                if selected[int(user_input)] == " ":
                    selected[int(user_input)] = "*"
                else:
                    selected[int(user_input)] = " "
        except:
            notify("Invalid selection ->" + user_input + "<-")

    pkgs = [options[s] for s in range(len(selected)) if selected[s] == '*']
    return pkgs
