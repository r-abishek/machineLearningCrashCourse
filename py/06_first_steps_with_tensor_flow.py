from __future__ import print_function

import math

from IPython import display
from matplotlib import cm
from matplotlib import gridspec
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from sklearn import metrics
import tensorflow as tf
from tensorflow.python.data import Dataset

tf.logging.set_verbosity(tf.logging.ERROR)
# pd.options.display.max_rows = 50
# pd.options.display.max_columns = 50
# pd.options.display.float_format = '{:.1f}'.format

# pd.set_option('display.max_rows', -1)
# pd.set_option('display.max_columns', -1)
# pd.set_option('precision', 2)

# Load Dataset
california_housing_dataframe = pd.read_csv("https://storage.googleapis.com/mledu-datasets/california_housing_train.csv", sep = ",", engine = "python")
print("\n\nDataframe:\n", california_housing_dataframe.head())

# Randomize the data
california_housing_dataframe = california_housing_dataframe.reindex(
    np.random.permutation(california_housing_dataframe.index)
)
print("\n\nDataframe Shuffled:\n", california_housing_dataframe.head())

# Scale median_house_value to be in thousands
california_housing_dataframe["median_house_value"] /= 1000.0
print("\n\nDataframe scaled:\n", california_housing_dataframe.head())

# Print a summary
print("\nDataframe Description:\n", california_housing_dataframe.describe())

# Define the input feature: total_rooms
my_feature = california_housing_dataframe[["total_rooms"]]

# Configure a numeric feature column for total_rooms
feature_columns = [tf.feature_column.numeric_column("total_rooms")]

# Define the label or target as median_house_value
targets = california_housing_dataframe["median_house_value"]

# Use gradient descent as the optimizer for training the model
my_optimizer = tf.train.GradientDescentOptimizer(learning_rate = 0.0000001)

# Clip gradients in the optimizer to avoid exploding gradients
my_optimizer = tf.contrib.estimator.clip_gradients_by_norm(my_optimizer, 5.0)

# Configure the linear regression model with our feature columns and optimizer
linear_regressor = tf.estimator.LinearRegressor(
    feature_columns = feature_columns,
    optimizer = my_optimizer
)

# Function to train a linear regression model of one feature
def my_input_fn(features, targets, batch_size = 1, shuffle = True, num_epochs = None):
    """
    Args:
        features: pandas dataframe of features
        targets: pandas dataframe of targets
        batch_size = size of batches
        shuffle = True/False
        num_epochs = Number of epochs
    Returns:
        Tuple of (features, labels) for next data batch
    """

    # Convert pandas data into a dict of np arrays
    features = {key:np.array(value) for key, value in dict(features).items()}

    # Construct a dataset, and configure batching / repeating
    ds = Dataset.from_tensor_slices((features, targets)) # 2GB limit
    ds = ds.batch(batch_size).repeat(num_epochs)

    # Shuffle the data, if specified
    if shuffle:
        ds = ds.shuffle(buffer_size = 10000)
    
    # Return the next batch of data
    features, labels = ds.make_one_shot_iterator().get_next()
    return features, labels

# Train the model
_ = linear_regressor.train(
    input_fn = lambda : my_input_fn(my_feature, targets),
    steps = 100
)

# Create an input function for predictions
prediction_input_fn = lambda : my_input_fn(my_feature, targets, num_epochs = 1, shuffle = False)

# Call predict() on the linear_regressor to make predictions
predictions = linear_regressor.predict(input_fn = prediction_input_fn)

# Format predicitons as a Numpy array, so that we can calcualte error metrics
predictions = np.array([item['predictions'][0] for item in predictions])

# Print MSE and RMSE
mse = metrics.mean_squared_error(predictions, targets)
rmse = math.sqrt(mse)
print ("\n\nMean Squared Error (on training data): %0.3f" % mse)
print ("Root Mean Squared Error (on training data): %0.3f" % rmse)

# Compare RMSE to the difference of the min and max of our targets
min_house_value = california_housing_dataframe["median_house_value"].min()
max_house_value = california_housing_dataframe["median_house_value"].max()
min_max_difference = max_house_value - min_house_value
print("Min. Median House Value: %0.3f" % min_house_value)
print("Max. Median House Value: %0.3f" % max_house_value)
print("Difference between Min. and Max.: %0.3f" % min_max_difference)
print("Root Mean Squared Error: %0.3f" % rmse)

# Print summary statistics on how well the predictions match targets
caliberation_data = pd.DataFrame()
caliberation_data["predictions"] = pd.Series(predictions)
caliberation_data["targets"] = pd.Series(targets)
caliberation_data.describe()

# Get a uniform random sample of the data to create a readable scatter plot
sample = california_housing_dataframe.sample(n = 300)

# Get the min and max total_rooms values.
x_0 = sample["total_rooms"].min()
x_1 = sample["total_rooms"].max()

# Retrieve the final weight and bias generated during training.
weight = linear_regressor.get_variable_value('linear/linear_model/total_rooms/weights')[0]
bias = linear_regressor.get_variable_value('linear/linear_model/bias_weights')

# Get the predicted median_house_values for the min and max total_rooms values.
y_0 = weight * x_0 + bias 
y_1 = weight * x_1 + bias

# Plot our regression line from (x_0, y_0) to (x_1, y_1).
plt.plot([x_0, x_1], [y_0, y_1], c='r')

# Label the graph axes.
plt.ylabel("median_house_value")
plt.xlabel("total_rooms")

# Plot a scatter plot from our data sample.
plt.scatter(sample["total_rooms"], sample["median_house_value"])

# Display graph.
plt.show()