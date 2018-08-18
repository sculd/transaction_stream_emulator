from pyspark.context import SparkContext

sc = SparkContext('local', 'test')

path = os.path.join(tempdir, "test.txt")
sc.addFile(path)

def func(iterator):
	with open(SparkFiles.get("test.txt")) as testFile:
		fileVal = int(testFile.readline())
		return [x * fileVal for x in iterator]

sc.parallelize([1, 2, 3, 4]).mapPartitions(func).collect()

