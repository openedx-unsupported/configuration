import click


@click.command()
@click.option('--username', envvar='USERNAME')
def great(username):
    print "++++++++++++++++++++"
    print username
    print "+++++++++++++++++++++"


if __name__ == '__main__':
    great()

