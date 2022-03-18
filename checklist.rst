リリース手順
==============

事前準備
--------------

* TestPyPIのアカウントを取得する
* PyPIのアカウントを取得する
* Githubアカウントに、bpmailerの編集権限を付与してもらう
* パッケージのビルドに使用するパッケージをインストールする

::

  $pip install wheel twine


リリース手順
--------------------
1. 次バージョンのパッケージをビルドし、パッケージが作成できることを確認する

::

  $ python setup.py sdist bdist_wheel
  $ ls dist
  bpmailer-1.2-py3-none-any.whl   bpmailer-1.2.tar.gz

2. twineのコマンドを実行して、PyPIでパッケージのドキュメントを正しく表示できそうか確認する

::

  $ twine check --strict dist/*
  Checking dist/bpmailer-1.2-py3-none-any.whl: PASSED
  Checking dist/bpmailer-1.2.tar.gz: PASSED

3. TestPyPIにアップロードする

::

  $ python -m twine upload --repository testpypi dist/*

4. TestPyPIの表示を確認する。(例: https://test.pypi.org/project/bpmailer/1.2/)

5. もしTestPyPIでの表示が正しくない場合、下記の「備考」を参考にパッケージのバージョンを変更して再度アップロードする

6. ローカル環境にてpipでTestPyPIからアップロードしたパッケージがインストールできることを確認する

::

  $ pip install Django~=2.2 Celery~=4.1 six
  $ pip install -i https://test.pypi.org/simple/ bpmailer
  $ pip freeze | grep bpmailer
  bpmailer==1.2.post3

7. Githubで次バージョンのRelaseタグを作成して、Publish Releaseする
8. 本番アップロード用のパッケージをビルドし、パッケージ名を確認する

::

  $ python setup.py sdist bdist_wheel
  $ ls dist
  bpmailer-1.2-py3-none-any.whl   bpmailer-1.2.tar.gz


9. PyPIにアップロードする

::

  $ python -m twine upload dist/*

備考
======

TestPyPIに同じバージョンで、再アップロードしたい時
--------------------------------------------------

postN(Post-release segment)のバージョン番号を変更して再度アップロードする

次の postNの部分を、post1, post2, post3 ...などと変更する)

::

  python setup.py egg_info --tag-build=postN sdist bdist_wheel



