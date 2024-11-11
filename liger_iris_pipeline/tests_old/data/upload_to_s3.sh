# Upload data files to public test data bucket on Amazon S3
# See https://zonca.github.io/2019/08/large-files-python-packages.html
s3cmd put --reduced-redundancy --acl-public "$@" s3://tmt-test-data/iris_pipeline/
