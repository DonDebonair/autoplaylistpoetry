from autoplaylistpoetry import create_app

__author__ = 'Daan Debie'

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)