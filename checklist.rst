リリース手順
==============


前提条件
--------------

* TestPyPIのアカウントを取得している
* PyPIのアカウントを取得している
* Githubアカウントに、bpmailerの編集権限を付与してもらう

PyPIにアップロードする準備作業
-------------------------------

ローカル環境で次のパッケージをインストールしておく
pip install wheel twine

リリース手順
-----------------
1. python setup.py sdist bdist_wheel
2. distディレクトリ配下に tar.gz と whl ファイルが作成されたことを確認する

::

  $ ls dist
  bpmailer-1.2-py3-none-any.whl   bpmailer-1.2.tar.gz

3. long_description で指定したドキュメントがPyPIで正しく表示されるかを確認する

::

  $ twine check --strict dist/*


参考: https://twine.readthedocs.io/en/stable/#twine-check

4. TestPyPIにアップロードする

::

  $ python -m twine upload --repository testpypi dist/*

5. xxx

TestPyPIに同じバージョンで、再アップロードしたい時
--------------------------------------------------

* postN(Post-release segment)のバージョン番号を変更して再度アップロードします。

  * .postNバージョン: 大元のバージョン番号を変えずに別バージョンで上げたい場合などに使う
  * `Post-release segment <https://peps.python.org/pep-0440/#public-version-identifiers>`_

次の postNの部分を、post1, post2, post3 ...などと変更する)

::

  python setup.py egg_info --tag-build=postN sdist bdist_wheel



