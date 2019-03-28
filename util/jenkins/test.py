import click


@click.command()
@click.option('--username', envvar='USERNAME')
@click.option('--password', envvar='PASSWORD')
def great(username):
    print "++++++++++++++++++++"
    print username
    print password
    print "+++++++++++++++++++++"


if __name__ == '__main__':
    great()

