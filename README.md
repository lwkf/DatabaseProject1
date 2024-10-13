# INF2003 Database Management System Group Project 1
## Group 20
### Project Name: INFMovieDB
### Team members:
| Full Name | Student ID |
| ----------- | ----------- |
| NG WEI HERNG  | 2302854 |
| CHNG SONG HENG ALOYSIUS | 2302857 |
|HENG YU XIN | 2302786 |
| WONG KHIN FOONG | 2302728 |
| WONG JUN KAI | 2302765 |

### Date submitted: 13 October 2024

# User Manual
### Note:
The API Keys provided are personal and are meant to provide a smoother set up for the person marking. These API Keys are for the Flask app and pulling in the Posters for the Motion Pictures.

## Step 1: Installing Requirements
Install the dependencies and libraries our app requires.
```
pip install -r requirements.txt
```

### Start Up Notes:
When the app runs for the first time, it checks whether "database.db" exists.

If it does not exist, it runs "init_db.py" which runs "schema.sql" and inserts the contents of "movie_data.csv" and "movie_credits.csv". It will also create 2 accounts, 1 with admin permissions and the other without. Along side, it will create 2 dummy comments under the movie "Inception".

## Step 2: Run App
Find and run the file "run_debug_flask.cmd"

## Step 3: Access the link on a browser
Find the local address of where the Flask App is being hosted at

Default Address:
```
http://127.0.0.1:5000
```

## Step 4: Different Access Levels
There are 3 types of users: Not Logged In, Logged In and Admin.

Here are the account details for our preset accounts:
| Email | Password |
| ----------- | ----------- |
| user@example.com | INF2003UserPWD |
| admin@example.com | INF2003AdminPWD |

### Not Logged In User
Users will only be able to View (READ) through Movies and Shows.

Users will be able to access the catalogue and be able to:

    1. Search for Titles through the Search Bar
    2. Select different types of Options for Genres, Release Years, Production Countries, Types of Motion Picture and Age Rating.
    3. Press Search to Filter the database for matching Motion Pictures based on selected Options.

They will not be able to leave behind comments.

They will be able to CREATE a new account requiring:

    1. Username
    2. Email
    3. Password

### Logged In User
Users can do all of what a Not Logged In User can do except registering. They have to log out first.

They will be able to comment, comment on comments and "delete" their own comments. 

The deletion of comments is not a DELETE but rather an UPDATE to change the contents of the comment to "[DELETED]".

They will be able to view their own Profile that contains their Username, Email and past Comments through the profile icon and username on the right of the Navigation bar.

Comments will have a clickable Title link of which Movie/Show they was posted in and a Timestamp of when they were posted.

Users will be able to delete their past Comments through their profile.

Users will be able to log out through the log out button on the right of the Navigation bar.

### Admin User
Admins can do all of what a Logged In User can do.

Admins will be able to DELETE Movies and Shows.
