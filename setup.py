from setuptools import setup, find_packages

version = '1.0'

setup(
    name='stubydoo',
    version=version,
    description='',
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
    ],
    keywords='',
    author='TN Tecnologia e Negocios',
    author_email='ed@tecnologiaenegocios.com.br',
    url='http://www.tecnologiaenegocios.com.br',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
    ],
)
