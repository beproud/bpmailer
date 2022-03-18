リリース手順
==============

事前準備
--------------

* TestPyPIのアカウントを取得する
* PyPIのアカウントを取得する
* Githubアカウントに、bpmailerの編集権限を付与してもらう
* pip install wheel twine


リリース手順
--------------------
1. python setup.py sdist bdist_wheel
2. distディレクトリ配下に tar.gz と whl ファイルが作成されたことを確認する

::

  $ ls dist
  bpmailer-1.2-py3-none-any.whl   bpmailer-1.2.tar.gz

3. long_description で指定したドキュメントがPyPIで正しく表示されるかを確認する

::

  $ twine check --strict dist/*


4. TestPyPIにアップロードする

::

  $ python -m twine upload --repository testpypi dist/*

5. TestPyPIの表示を確認する。例: https://test.pypi.org/project/bpmailer/1.2.post3/


備考
======

TestPyPIに同じバージョンで、再アップロードしたい時
--------------------------------------------------

postN(Post-release segment)のバージョン番号を変更して再度アップロードする。

次の postNの部分を、post1, post2, post3 ...などと変更する)

::

  python setup.py egg_info --tag-build=postN sdist bdist_wheel



