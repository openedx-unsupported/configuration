import click


@click.command()
@click.option('--username', envvar='USERNAME')
def great(username):
    print username


if __name__ == '__main__':
    great()

