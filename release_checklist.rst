リリース手順
==============

事前準備
--------------

* GitHub, PyPI, TestPyPIのアカウントにbpmailerの編集権限を設定
* パッケージのビルドに使用するパッケージをインストールする

  * ``pip install wheel twine``


手順
--------------------
1. 次バージョンのパッケージをビルドする

   * ``python setup.py sdist bdist_wheel``

2. twineのコマンドを実行して、エラーが出ないことを確認する

   * ``twine check --strict dist/*``

3. dist/に作成したパッケージをTestPyPIへアップロードする

   * ``twine upload --repository testpypi dist/*``

4. TestPyPIで、descriptionがエラーなく表示されていることと、ビルドしたパッケージがアップロードされていることを確認する

   * もしTestPyPIへアップロードした内容に問題がある場合、そのパッケージを削除し、postN(Post-release segment)のバージョン番号を付加したパッケージをTestPyPIに再度アップロードする
   * ``rm -fr dist``
   * ``python setup.py egg_info --tag-build=postN sdist bdist_wheel`` (postN: post1, post2..)
   * ``twine upload --repository testpypi dist/*``

5. ローカル環境にて、TestPyPIにアップロードしたパッケージがインストール可能であることを確認する

   * ``pip install Django~=2.2 Celery~=4.1.0 six``
   * ``pip install -i https://test.pypi.org/simple/ bpmailer``
   * ``pip show bpmailer``

6. GitHubで次バージョンのReleaseタグを作成し、Publish Releaseする

   * もしdist/にpostNバージョンがついたパッケージが残っている場合、それらのパッケージを全て削除し、本番アップロード用のパッケージを再度作成する
   * ``rm -fr dist``
   * ``python setup.py sdist bdist_wheel``

7. dist/に作成したパッケージを本番環境のPyPIにアップロードする

   * ``twine upload dist/*``
