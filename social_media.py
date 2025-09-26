import mysql.connector
from mysql.connector import Error
import bcrypt

class SocialMediaApp:
    def __init__(self):
        self.connection = None
        self.current_user = None

    def connect_to_database(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database='social_media_db',
                user='root',
                password='sanjay05'
            )

            if self.connection.is_connected():
                print("Successfully connected to the database")
                return True

        except Error as e:
            print(f"Error while connecting to MySQL: {e}")
            return False

    def hash_password(self, password):
        # Hash a password for storing
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password, hashed):
        # Check hashed password
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def login(self):
        print("\n=== LOGIN ===")
        username = input("Enter your username: ")
        password = input("Enter your password: ")

        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM Users WHERE Username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if user and self.check_password(password, user['PasswordHash']):
                self.current_user = user
                print(f"Login successful! Welcome {user['Name']}!")
                return True
            else:
                print("Invalid username or password.")
                return False

        except Error as e:
            print(f"Error during login: {e}")
            return False

    def signup(self):
        print("\n=== SIGN UP ===")
        username = input("Choose a username: ")
        email = input("Enter your email: ")
        password = input("Choose a password: ")
        name = input("Enter your full name: ")
        gender = input("Enter your gender (M/F/O): ")
        dob = input("Enter your date of birth (YYYY-MM-DD): ")
        bio = input("Enter a short bio: ")
        is_private = input("Make account private? (Y/N): ")

        try:
            cursor = self.connection.cursor(dictionary=True)

            # Check if username already exists
            check_query = "SELECT * FROM Users WHERE Username = %s OR Email = %s"
            cursor.execute(check_query, (username, email))
            if cursor.fetchone():
                print("Username or email already exists!")
                return False

            # Hash password
            hashed_password = self.hash_password(password)

            # Insert into Users table
            user_query = """
            INSERT INTO Users (Username, Email, PasswordHash, Name, Gender, DOB, Bio, IsPrivate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(user_query, (username, email, hashed_password, name, gender, dob, bio, is_private))
            user_id = cursor.lastrowid

            # Insert into UserProfile table
            profile_query = """
            INSERT INTO UserProfile (UserID, About)
            VALUES (%s, %s)
            """
            cursor.execute(profile_query, (user_id, bio))

            self.connection.commit()
            print("Account created successfully! You can now login.")
            return True

        except Error as e:
            print(f"Error during signup: {e}")
            self.connection.rollback()
            return False

    def main_menu(self):
        while True:
            print("\n=== SOCIAL MEDIA APPLICATION ===")
            print("1. Sign Up (New User)")
            print("2. Login (Existing User)")
            print("9. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                if self.signup():
                    # After successful signup, ask to login
                    if self.login():
                        self.user_dashboard()
            elif choice == '2':
                if self.login():
                    self.user_dashboard()
            elif choice == '9':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    def user_dashboard(self):
        print(f"\n=== WELCOME {self.current_user['Name']} ===")

        while True:
            print("\n1. View Profile")
            print("2. View My Posts")
            print("3. Create Post")
            print("4. View Notifications")
            print("5. Browse Posts (One by One)")
            print("6. Search User")
            print("7. View Liked Posts")
            print("8. Edit Profile")
            print("9. Change Password")
            print("10. View Followers")
            print("11. View Following")
            print("12. Delete Account")
            print("13. Manage Follow Requests")
            print("14. View Post Shares")
            print("15. Logout")

            choice = input("Enter your choice: ")

            if choice == '1':
                self.view_profile()
            elif choice == '2':
                self.view_my_posts()
            elif choice == '3':
                self.create_post()
            elif choice == '4':
                self.view_notifications()
            elif choice == '5':
                self.browse_posts()
            elif choice == '6':
                self.search_user()
            elif choice == '7':
                self.view_liked_posts()
            elif choice == '8':
                self.edit_profile()
            elif choice == '9':
                self.change_password()
            elif choice == '10':
                self.view_followers()
            elif choice == '11':
                self.view_following()
            elif choice == '12':
                self.delete_account()
            elif choice == '13':
                self.manage_follow_requests()
            elif choice == '14':
                self.view_post_shares()
            elif choice == '15':
                print("Logging out...")
                self.current_user = None
                break
            else:
                print("Invalid choice. Please try again.")

    def view_profile(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.*, up.AvatarURL, up.Website, up.Location, up.About 
            FROM Users u 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID 
            WHERE u.UserID = %s
            """
            cursor.execute(query, (self.current_user['UserID'],))
            profile = cursor.fetchone()

            print(f"\n=== YOUR PROFILE ===")
            print(f"Name: {profile['Name']}")
            print(f"Username: {profile['Username']}")
            print(f"Email: {profile['Email']}")
            print(f"Gender: {profile['Gender']}")
            print(f"Date of Birth: {profile['DOB']}")
            print(f"Bio: {profile['Bio']}")
            print(f"Location: {profile['Location']}")
            print(f"Website: {profile['Website']}")
            print(f"About: {profile['About']}")
            print(f"Account Type: {'Private' if profile['IsPrivate'] == 'Y' else 'Public'}")

            # Show followers and following count
            followers_query = "SELECT COUNT(*) as count FROM Followers WHERE UserID = %s AND Status = 'accepted'"
            cursor.execute(followers_query, (self.current_user['UserID'],))
            followers = cursor.fetchone()['count']

            following_query = "SELECT COUNT(*) as count FROM Followers WHERE FollowerUserID = %s AND Status = 'accepted'"
            cursor.execute(following_query, (self.current_user['UserID'],))
            following = cursor.fetchone()['count']

            # Show pending follow requests
            pending_query = "SELECT COUNT(*) as count FROM Followers WHERE UserID = %s AND Status = 'pending'"
            cursor.execute(pending_query, (self.current_user['UserID'],))
            pending = cursor.fetchone()['count']

            print(f"Followers: {followers}")
            print(f"Following: {following}")
            print(f"Pending Follow Requests: {pending}")

        except Error as e:
            print(f"Error viewing profile: {e}")

    def view_my_posts(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT p.*, u.Username, u.Name 
            FROM Posts p 
            JOIN Users u ON p.UserID = u.UserID 
            WHERE p.UserID = %s
            ORDER BY p.CreatedAt DESC
            """
            cursor.execute(query, (self.current_user['UserID'],))
            posts = cursor.fetchall()

            if not posts:
                print("You haven't created any posts yet.")
                return

            print(f"\n=== MY POSTS ===")
            for post in posts:
                print(f"\n{post['Name']} (@{post['Username']}) - {post['CreatedAt']}")
                print(f"Content: {post['Content']}")

                # Show media if exists
                media_query = "SELECT * FROM Media WHERE PostID = %s"
                cursor.execute(media_query, (post['PostID'],))
                media = cursor.fetchall()

                for m in media:
                    print(f"Media: {m['MediaURL']} ({m['MediaType']})")

                # Show likes and comments count
                likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
                cursor.execute(likes_query, (post['PostID'],))
                likes = cursor.fetchone()['count']

                comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
                cursor.execute(comments_query, (post['PostID'],))
                comments = cursor.fetchone()['count']

                # Show shares count
                shares_query = "SELECT COUNT(*) as count FROM Shares WHERE PostID = %s"
                cursor.execute(shares_query, (post['PostID'],))
                shares = cursor.fetchone()['count']

                print(f"Likes: {likes} | Comments: {comments} | Shares: {shares}")
                print("---")

        except Error as e:
            print(f"Error viewing posts: {e}")

    def create_post(self):
        content = input("What's on your mind? ")
        media_url = input("Enter media URL (optional): ")
        media_type = input("Enter media type (image/video, optional): ") if media_url else None

        try:
            cursor = self.connection.cursor(dictionary=True)
            post_query = "INSERT INTO Posts (UserID, Content) VALUES (%s, %s)"
            cursor.execute(post_query, (self.current_user['UserID'], content))
            post_id = cursor.lastrowid

            if media_url and media_type:
                media_query = "INSERT INTO Media (PostID, MediaURL, MediaType) VALUES (%s, %s, %s)"
                cursor.execute(media_query, (post_id, media_url, media_type))

            self.connection.commit()
            print("Post created successfully!")

        except Error as e:
            print(f"Error creating post: {e}")

    def view_notifications(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT n.*, u.Username as SenderUsername, u.Name as SenderName
            FROM Notifications n 
            JOIN Users u ON n.SenderID = u.UserID 
            WHERE n.ReceiverID = %s 
            ORDER BY n.CreatedAt DESC
            """
            cursor.execute(query, (self.current_user['UserID'],))
            notifications = cursor.fetchall()

            print(f"\n=== NOTIFICATIONS ===")
            if notifications:
                for notification in notifications:
                    # Try to get sender's avatar
                    avatar_query = "SELECT AvatarURL FROM UserProfile WHERE UserID = %s"
                    cursor.execute(avatar_query, (notification['SenderID'],))
                    avatar = cursor.fetchone()

                    avatar_url = avatar['AvatarURL'] if avatar and avatar['AvatarURL'] else "No avatar"

                    print(f"{notification['SenderName']} (@{notification['SenderUsername']}) {notification['Message']}")
                    print(f"Avatar: {avatar_url}")
                    print(f"Time: {notification['CreatedAt']}")

                    # For follow requests, show options to accept/reject
                    if notification['Type'] == 'follow_request':
                        print("Options: A - Accept, R - Reject")

                    print("---")
            else:
                print("No notifications")

            # Check if user wants to respond to any follow requests
            respond = input("Would you like to respond to any follow requests? (Y/N): ")
            if respond.upper() == 'Y':
                self.manage_follow_requests()

        except Error as e:
            print(f"Error viewing notifications: {e}")

    def browse_posts(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT p.*, u.Username, u.Name 
            FROM Posts p 
            JOIN Users u ON p.UserID = u.UserID 
            ORDER BY p.CreatedAt DESC
            """
            cursor.execute(query)
            posts = cursor.fetchall()

            if not posts:
                print("No posts available to browse. Be the first to create a post!")
                return

            current_index = 0
            while current_index < len(posts):
                post = posts[current_index]

                # Display post with clear separation
                print("\n" + "=" * 60)
                print(f"=== POST {current_index + 1} OF {len(posts)} ===")
                print("=" * 60)
                print(f"{post['Name']} (@{post['Username']}) - {post['CreatedAt']}")
                print(f"Content: {post['Content']}")

                # Show media if exists
                media_query = "SELECT * FROM Media WHERE PostID = %s"
                cursor.execute(media_query, (post['PostID'],))
                media = cursor.fetchall()

                for m in media:
                    print(f"Media: {m['MediaURL']} ({m['MediaType']})")

                # Show likes, comments, and shares count
                likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
                cursor.execute(likes_query, (post['PostID'],))
                likes = cursor.fetchone()['count']

                comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
                cursor.execute(comments_query, (post['PostID'],))
                comments = cursor.fetchone()['count']

                shares_query = "SELECT COUNT(*) as count FROM Shares WHERE PostID = %s"
                cursor.execute(shares_query, (post['PostID'],))
                shares = cursor.fetchone()['count']

                # Check if current user has liked this post
                user_like_query = "SELECT * FROM Likes WHERE PostID = %s AND UserID = %s"
                cursor.execute(user_like_query, (post['PostID'], self.current_user['UserID']))
                user_liked = cursor.fetchone() is not None

                print(f"Likes: {likes} | Comments: {comments} | Shares: {shares}")
                if user_liked:
                    print("You have liked this post")

                print("\nOptions:")
                print("L - Like/Unlike this post")
                print("C - Comment on this post")
                print("F - Follow this user")
                print("S - Share this post")
                print("V - View comments for this post")
                print("W - View who shared this post")
                print("N - Next post")
                print("P - Previous post")
                print("E - Exit to dashboard")

                choice = input("Enter your choice: ").upper()

                if choice == 'L':
                    self.toggle_like(post['PostID'])
                    # Refresh the post data
                    cursor.execute(query)
                    posts = cursor.fetchall()
                elif choice == 'C':
                    self.add_comment(post['PostID'])
                    # Refresh the post data
                    cursor.execute(query)
                    posts = cursor.fetchall()
                elif choice == 'F':
                    self.send_follow_request(post['UserID'])
                elif choice == 'S':
                    self.share_post(post['PostID'])
                elif choice == 'V':
                    self.view_post_comments(post['PostID'])
                elif choice == 'W':
                    self.view_post_shares_details(post['PostID'])
                elif choice == 'N':
                    current_index += 1
                elif choice == 'P':
                    if current_index > 0:
                        current_index -= 1
                    else:
                        print("You're already at the first post.")
                elif choice == 'E':
                    break
                else:
                    print("Invalid choice. Please try again.")

        except Error as e:
            print(f"Error browsing posts: {e}")

    def toggle_like(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Check if user already liked this post
            check_query = "SELECT * FROM Likes WHERE PostID = %s AND UserID = %s"
            cursor.execute(check_query, (post_id, self.current_user['UserID']))
            existing_like = cursor.fetchone()

            if existing_like:
                # Unlike the post
                delete_query = "DELETE FROM Likes WHERE PostID = %s AND UserID = %s"
                cursor.execute(delete_query, (post_id, self.current_user['UserID']))
                print("Post unliked.")
            else:
                # Like the post
                insert_query = "INSERT INTO Likes (PostID, UserID) VALUES (%s, %s)"
                cursor.execute(insert_query, (post_id, self.current_user['UserID']))

                # Create notification for the post owner
                # First get post owner ID
                post_query = "SELECT UserID FROM Posts WHERE PostID = %s"
                cursor.execute(post_query, (post_id,))
                post_owner = cursor.fetchone()

                if post_owner and post_owner['UserID'] != self.current_user['UserID']:
                    notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                    cursor.execute(notif_query,
                                   (self.current_user['UserID'], post_owner['UserID'], 'liked your post', 'like'))

                print("Post liked.")

            self.connection.commit()

        except Error as e:
            print(f"Error toggling like: {e}")

    def add_comment(self, post_id):
        try:
            comment_text = input("Enter your comment: ")

            cursor = self.connection.cursor(dictionary=True)
            query = "INSERT INTO Comments (PostID, UserID, TextComment) VALUES (%s, %s, %s)"
            cursor.execute(query, (post_id, self.current_user['UserID'], comment_text))

            # Create notification for the post owner
            # First get post owner ID
            post_query = "SELECT UserID FROM Posts WHERE PostID = %s"
            cursor.execute(post_query, (post_id,))
            post_owner = cursor.fetchone()

            if post_owner and post_owner['UserID'] != self.current_user['UserID']:
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], post_owner['UserID'], 'commented on your post', 'comment'))

            self.connection.commit()
            print("Comment added successfully!")

        except Error as e:
            print(f"Error adding comment: {e}")

    def view_post_comments(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT c.*, u.Username, u.Name 
            FROM Comments c 
            JOIN Users u ON c.UserID = u.UserID 
            WHERE c.PostID = %s 
            ORDER BY c.CreatedAt DESC
            """
            cursor.execute(query, (post_id,))
            comments = cursor.fetchall()

            print(f"\n=== COMMENTS FOR POST ===")
            if comments:
                for comment in comments:
                    print(f"\n{comment['Name']} (@{comment['Username']}) - {comment['CreatedAt']}")
                    print(f"Comment: {comment['TextComment']}")
                    print("---")
            else:
                print("No comments for this post.")

        except Error as e:
            print(f"Error viewing comments: {e}")

    def view_post_shares_details(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT s.*, u.Username, u.Name 
            FROM Shares s 
            JOIN Users u ON s.UserID = u.UserID 
            WHERE s.PostID = %s 
            ORDER BY s.SharedAt DESC
            """
            cursor.execute(query, (post_id,))
            shares = cursor.fetchall()

            print(f"\n=== SHARES FOR POST ===")
            if shares:
                for share in shares:
                    print(f"\n{share['Name']} (@{share['Username']}) - {share['SharedAt']}")
                    if share['Message']:
                        print(f"Message: {share['Message']}")
                    print("---")
            else:
                print("This post hasn't been shared yet.")

        except Error as e:
            print(f"Error viewing post shares: {e}")

    def view_post_shares(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT p.PostID, p.Content, COUNT(s.ShareID) as share_count
            FROM Posts p 
            LEFT JOIN Shares s ON p.PostID = s.PostID 
            WHERE p.UserID = %s
            GROUP BY p.PostID
            HAVING share_count > 0
            ORDER BY share_count DESC
            """
            cursor.execute(query, (self.current_user['UserID'],))
            posts_with_shares = cursor.fetchall()

            if not posts_with_shares:
                print("Your posts haven't been shared yet.")
                return

            print(f"\n=== YOUR POSTS THAT HAVE BEEN SHARED ===")
            for i, post in enumerate(posts_with_shares):
                print(f"\n{i + 1}. Post: {post['Content'][:50]}...")
                print(f"   Share Count: {post['share_count']}")

            print("\nOptions:")
            print("V - View who shared a post")
            print("B - Back to dashboard")

            choice = input("Enter your choice: ").upper()

            if choice == 'V':
                try:
                    post_num = int(input("Enter the number of the post you want to view shares for: "))
                    if 1 <= post_num <= len(posts_with_shares):
                        self.view_post_shares_details(posts_with_shares[post_num - 1]['PostID'])
                    else:
                        print("Invalid post number.")
                except ValueError:
                    print("Please enter a valid number.")
            elif choice == 'B':
                return
            else:
                print("Invalid choice.")

        except Error as e:
            print(f"Error viewing post shares: {e}")

    def view_liked_posts(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT p.*, u.Username, u.Name 
            FROM Posts p 
            JOIN Likes l ON p.PostID = l.PostID
            JOIN Users u ON p.UserID = u.UserID
            WHERE l.UserID = %s
            ORDER BY l.Timestamp DESC
            """
            cursor.execute(query, (self.current_user['UserID'],))
            posts = cursor.fetchall()

            if not posts:
                print("You haven't liked any posts yet.")
                return

            print(f"\n=== POSTS YOU'VE LIKED ===")
            for i, post in enumerate(posts):
                print(f"\n{i + 1}. {post['Name']} (@{post['Username']}) - {post['CreatedAt']}")
                print(f"   Content: {post['Content']}")

                # Show media if exists
                media_query = "SELECT * FROM Media WHERE PostID = %s"
                cursor.execute(media_query, (post['PostID'],))
                media = cursor.fetchall()

                for m in media:
                    print(f"   Media: {m['MediaURL']} ({m['MediaType']})")

                # Show likes and comments count
                likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
                cursor.execute(likes_query, (post['PostID'],))
                likes = cursor.fetchone()['count']

                comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
                cursor.execute(comments_query, (post['PostID'],))
                comments = cursor.fetchone()['count']

                print(f"   Likes: {likes} | Comments: {comments}")

            print("\nOptions:")
            print("U - Unlike a post")
            print("V - View a post")
            print("B - Back to dashboard")

            choice = input("Enter your choice: ").upper()

            if choice == 'U':
                try:
                    post_num = int(input("Enter the number of the post you want to unlike: "))
                    if 1 <= post_num <= len(posts):
                        unlike_query = "DELETE FROM Likes WHERE PostID = %s AND UserID = %s"
                        cursor.execute(unlike_query, (posts[post_num - 1]['PostID'], self.current_user['UserID']))
                        self.connection.commit()
                        print("Post unliked successfully!")
                    else:
                        print("Invalid post number.")
                except ValueError:
                    print("Please enter a valid number.")

            elif choice == 'V':
                try:
                    post_num = int(input("Enter the number of the post you want to view: "))
                    if 1 <= post_num <= len(posts):
                        self.view_single_post(posts[post_num - 1]['PostID'])
                    else:
                        print("Invalid post number.")
                except ValueError:
                    print("Please enter a valid number.")

            elif choice == 'B':
                return
            else:
                print("Invalid choice.")

        except Error as e:
            print(f"Error viewing liked posts: {e}")

    def view_single_post(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT p.*, u.Username, u.Name 
            FROM Posts p 
            JOIN Users u ON p.UserID = u.UserID 
            WHERE p.PostID = %s
            """
            cursor.execute(query, (post_id,))
            post = cursor.fetchone()

            if not post:
                print("Post not found.")
                return

            print(f"\n{post['Name']} (@{post['Username']}) - {post['CreatedAt']}")
            print(f"Content: {post['Content']}")

            # Show media if exists
            media_query = "SELECT * FROM Media WHERE PostID = %s"
            cursor.execute(media_query, (post_id,))
            media = cursor.fetchall()

            for m in media:
                print(f"Media: {m['MediaURL']} ({m['MediaType']})")

            # Show likes and comments count
            likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
            cursor.execute(likes_query, (post_id,))
            likes = cursor.fetchone()['count']

            comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
            cursor.execute(comments_query, (post_id,))
            comments = cursor.fetchone()['count']

            # Check if current user has liked this post
            user_like_query = "SELECT * FROM Likes WHERE PostID = %s AND UserID = %s"
            cursor.execute(user_like_query, (post_id, self.current_user['UserID']))
            user_liked = cursor.fetchone() is not None

            print(f"Likes: {likes} | Comments: {comments}")
            if user_liked:
                print("You have liked this post")

        except Error as e:
            print(f"Error viewing post: {e}")

    def edit_profile(self):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Get current profile data
            query = """
            SELECT u.*, up.AvatarURL, up.Website, up.Location, up.About 
            FROM Users u 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID 
            WHERE u.UserID = %s
            """
            cursor.execute(query, (self.current_user['UserID'],))
            profile = cursor.fetchone()

            while True:
                print("\n=== EDIT PROFILE ===")
                print("Select which attribute you want to update:")
                print("1. Name")
                print("2. Bio")
                print("3. Location")
                print("4. Website")
                print("5. About")
                print("6. Avatar URL")
                print("7. Privacy Setting")
                print("8. Back to dashboard")

                choice = input("Enter your choice: ")

                if choice == '1':
                    new_name = input(f"Enter new name ({profile['Name']}): ")
                    if new_name:
                        update_query = "UPDATE Users SET Name = %s WHERE UserID = %s"
                        cursor.execute(update_query, (new_name, self.current_user['UserID']))
                        self.connection.commit()
                        print("Name updated successfully!")

                elif choice == '2':
                    new_bio = input(f"Enter new bio ({profile['Bio']}): ")
                    if new_bio:
                        update_query = "UPDATE Users SET Bio = %s WHERE UserID = %s"
                        cursor.execute(update_query, (new_bio, self.current_user['UserID']))
                        self.connection.commit()
                        print("Bio updated successfully!")

                elif choice == '3':
                    new_location = input(f"Enter new location ({profile['Location'] or 'None'}): ")
                    update_query = "UPDATE UserProfile SET Location = %s WHERE UserID = %s"
                    cursor.execute(update_query, (new_location, self.current_user['UserID']))
                    self.connection.commit()
                    print("Location updated successfully!")

                elif choice == '4':
                    new_website = input(f"Enter new website ({profile['Website'] or 'None'}): ")
                    update_query = "UPDATE UserProfile SET Website = %s WHERE UserID = %s"
                    cursor.execute(update_query, (new_website, self.current_user['UserID']))
                    self.connection.commit()
                    print("Website updated successfully!")

                elif choice == '5':
                    new_about = input(f"Enter new about ({profile['About'] or 'None'}): ")
                    update_query = "UPDATE UserProfile SET About = %s WHERE UserID = %s"
                    cursor.execute(update_query, (new_about, self.current_user['UserID']))
                    self.connection.commit()
                    print("About updated successfully!")

                elif choice == '6':
                    new_avatar = input(f"Enter new avatar URL ({profile['AvatarURL'] or 'None'}): ")
                    update_query = "UPDATE UserProfile SET AvatarURL = %s WHERE UserID = %s"
                    cursor.execute(update_query, (new_avatar, self.current_user['UserID']))
                    self.connection.commit()
                    print("Avatar URL updated successfully!")

                elif choice == '7':
                    current_setting = "Private" if profile['IsPrivate'] == 'Y' else "Public"
                    new_privacy = input(f"Change privacy setting ({current_setting}): (Y for Private, N for Public): ")
                    if new_privacy.upper() in ['Y', 'N']:
                        update_query = "UPDATE Users SET IsPrivate = %s WHERE UserID = %s"
                        cursor.execute(update_query, (new_privacy.upper(), self.current_user['UserID']))
                        self.connection.commit()
                        print("Privacy setting updated successfully!")
                    else:
                        print("Invalid input. Please enter Y or N.")

                elif choice == '8':
                    return

                else:
                    print("Invalid choice.")

                # Ask if user wants to continue editing
                continue_edit = input("Would you like to continue editing your profile? (Y/N): ")
                if continue_edit.upper() != 'Y':
                    break

                # Refresh profile data
                cursor.execute(query, (self.current_user['UserID'],))
                profile = cursor.fetchone()

        except Error as e:
            print(f"Error updating profile: {e}")
            self.connection.rollback()

    def change_password(self):
        try:
            current_password = input("Enter your current password: ")

            # Verify current password
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT PasswordHash FROM Users WHERE UserID = %s"
            cursor.execute(query, (self.current_user['UserID'],))
            user = cursor.fetchone()

            if not self.check_password(current_password, user['PasswordHash']):
                print("Current password is incorrect.")
                return

            new_password = input("Enter your new password: ")
            confirm_password = input("Confirm your new password: ")

            if new_password != confirm_password:
                print("Passwords do not match.")
                return

            # Hash new password
            hashed_password = self.hash_password(new_password)

            # Update password
            update_query = "UPDATE Users SET PasswordHash = %s WHERE UserID = %s"
            cursor.execute(update_query, (hashed_password, self.current_user['UserID']))
            self.connection.commit()

            print("Password changed successfully!")

        except Error as e:
            print(f"Error changing password: {e}")
            self.connection.rollback()

    def view_followers(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.UserID, u.Username, u.Name, u.Bio 
            FROM Users u 
            JOIN Followers f ON u.UserID = f.FollowerUserID 
            WHERE f.UserID = %s AND f.Status = 'accepted'
            """
            cursor.execute(query, (self.current_user['UserID'],))
            followers = cursor.fetchall()

            print(f"\n=== YOUR FOLLOWERS ===")
            if followers:
                for i, follower in enumerate(followers):
                    print(f"\n{i + 1}. {follower['Name']} (@{follower['Username']})")
                    print(f"   Bio: {follower['Bio']}")

                print("\nOptions:")
                print("U - Unfollow a follower")
                print("V - View a follower's profile")
                print("B - Back to dashboard")

                choice = input("Enter your choice: ").upper()

                if choice == 'U':
                    try:
                        follower_num = int(input("Enter the number of the follower you want to unfollow: "))
                        if 1 <= follower_num <= len(followers):
                            self.unfollow_user(followers[follower_num - 1]['UserID'])
                        else:
                            print("Invalid follower number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'V':
                    try:
                        follower_num = int(input("Enter the number of the follower whose profile you want to view: "))
                        if 1 <= follower_num <= len(followers):
                            self.view_user_profile(followers[follower_num - 1]['UserID'])
                        else:
                            print("Invalid follower number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'B':
                    return
                else:
                    print("Invalid choice.")
            else:
                print("You don't have any followers yet.")

        except Error as e:
            print(f"Error viewing followers: {e}")

    def view_following(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.UserID, u.Username, u.Name, u.Bio 
            FROM Users u 
            JOIN Followers f ON u.UserID = f.UserID 
            WHERE f.FollowerUserID = %s AND f.Status = 'accepted'
            """
            cursor.execute(query, (self.current_user['UserID'],))
            following = cursor.fetchall()

            print(f"\n=== USERS YOU FOLLOW ===")
            if following:
                for i, user in enumerate(following):
                    print(f"\n{i + 1}. {user['Name']} (@{user['Username']})")
                    print(f"   Bio: {user['Bio']}")

                print("\nOptions:")
                print("U - Unfollow a user")
                print("V - View a user's profile")
                print("B - Back to dashboard")

                choice = input("Enter your choice: ").upper()

                if choice == 'U':
                    try:
                        user_num = int(input("Enter the number of the user you want to unfollow: "))
                        if 1 <= user_num <= len(following):
                            self.unfollow_user(following[user_num - 1]['UserID'])
                        else:
                            print("Invalid user number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'V':
                    try:
                        user_num = int(input("Enter the number of the user whose profile you want to view: "))
                        if 1 <= user_num <= len(following):
                            self.view_user_profile(following[user_num - 1]['UserID'])
                        else:
                            print("Invalid user number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'B':
                    return
                else:
                    print("Invalid choice.")
            else:
                print("You're not following anyone yet.")

        except Error as e:
            print(f"Error viewing following: {e}")

    def unfollow_user(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Check if user exists
            user_query = "SELECT Username FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (user_id,))
            user = cursor.fetchone()

            if not user:
                print("User not found.")
                return

            # Check if actually following
            follow_query = "SELECT * FROM Followers WHERE UserID = %s AND FollowerUserID = %s AND Status = 'accepted'"
            cursor.execute(follow_query, (user_id, self.current_user['UserID']))
            existing_follow = cursor.fetchone()

            if not existing_follow:
                print(f"You are not following {user['Username']}.")
                return

            # Unfollow the user
            delete_query = "DELETE FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
            cursor.execute(delete_query, (user_id, self.current_user['UserID']))

            self.connection.commit()
            print(f"You have unfollowed {user['Username']}.")

        except Error as e:
            print(f"Error unfollowing user: {e}")
            self.connection.rollback()

    def delete_account(self):
        try:
            confirm = input("Are you sure you want to delete your account? This action cannot be undone. (yes/no): ")
            if confirm.lower() != 'yes':
                print("Account deletion cancelled.")
                return

            password = input("Enter your password to confirm: ")

            # Verify password
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT PasswordHash FROM Users WHERE UserID = %s"
            cursor.execute(query, (self.current_user['UserID'],))
            user = cursor.fetchone()

            if not self.check_password(password, user['PasswordHash']):
                print("Incorrect password. Account deletion cancelled.")
                return

            # Delete user (cascades to all related tables due to ON DELETE CASCADE)
            delete_query = "DELETE FROM Users WHERE UserID = %s"
            cursor.execute(delete_query, (self.current_user['UserID'],))
            self.connection.commit()

            print("Your account has been deleted successfully.")
            self.current_user = None

        except Error as e:
            print(f"Error deleting account: {e}")
            self.connection.rollback()

    def send_follow_request(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Check if user exists
            user_query = "SELECT Username, Name, IsPrivate FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (user_id,))
            user = cursor.fetchone()

            if not user:
                print("User not found.")
                return

            if user_id == self.current_user['UserID']:
                print("You cannot follow yourself.")
                return

            # Check if already following or request pending
            follow_query = "SELECT * FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
            cursor.execute(follow_query, (user_id, self.current_user['UserID']))
            existing_follow = cursor.fetchone()

            if existing_follow:
                if existing_follow['Status'] == 'accepted':
                    print(f"You are already following {user['Username']}.")
                elif existing_follow['Status'] == 'pending':
                    print(f"You have already sent a follow request to {user['Username']}.")
                elif existing_follow['Status'] == 'rejected':
                    print(f"Your previous follow request to {user['Username']} was rejected.")
                return

            # For public accounts, follow directly
            if user['IsPrivate'] == 'N':
                insert_query = "INSERT INTO Followers (UserID, FollowerUserID, Status, RespondedAt) VALUES (%s, %s, 'accepted', NOW())"
                cursor.execute(insert_query, (user_id, self.current_user['UserID']))

                # Create notification
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], user_id, 'started following you', 'follow_accept'))

                print(f"You are now following {user['Username']}.")
            else:
                # For private accounts, send follow request
                insert_query = "INSERT INTO Followers (UserID, FollowerUserID, Status) VALUES (%s, %s, 'pending')"
                cursor.execute(insert_query, (user_id, self.current_user['UserID']))

                # Create notification
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], user_id, 'sent you a follow request', 'follow_request'))

                print(f"Follow request sent to {user['Username']}. Waiting for approval.")

            self.connection.commit()

        except Error as e:
            print(f"Error sending follow request: {e}")
            self.connection.rollback()

    def manage_follow_requests(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT f.*, u.Username, u.Name 
            FROM Followers f 
            JOIN Users u ON f.FollowerUserID = u.UserID 
            WHERE f.UserID = %s AND f.Status = 'pending'
            """
            cursor.execute(query, (self.current_user['UserID'],))
            requests = cursor.fetchall()

            if not requests:
                print("You don't have any pending follow requests.")
                return

            print(f"\n=== PENDING FOLLOW REQUESTS ===")
            for i, request in enumerate(requests):
                print(f"\n{i + 1}. {request['Name']} (@{request['Username']})")
                print(f"   Requested at: {request['RequestedAt']}")

            print("\nOptions:")
            print("A - Accept a request")
            print("R - Reject a request")
            print("V - View a user's profile")
            print("B - Back to dashboard")

            choice = input("Enter your choice: ").upper()

            if choice == 'A':
                try:
                    req_num = int(input("Enter the number of the request you want to accept: "))
                    if 1 <= req_num <= len(requests):
                        self.respond_to_follow_request(requests[req_num - 1]['FollowerID'], 'accepted')
                    else:
                        print("Invalid request number.")
                except ValueError:
                    print("Please enter a valid number.")

            elif choice == 'R':
                try:
                    req_num = int(input("Enter the number of the request you want to reject: "))
                    if 1 <= req_num <= len(requests):
                        self.respond_to_follow_request(requests[req_num - 1]['FollowerID'], 'rejected')
                    else:
                        print("Invalid request number.")
                except ValueError:
                    print("Please enter a valid number.")

            elif choice == 'V':
                try:
                    req_num = int(input("Enter the number of the user whose profile you want to view: "))
                    if 1 <= req_num <= len(requests):
                        self.view_user_profile(requests[req_num - 1]['FollowerUserID'])
                    else:
                        print("Invalid request number.")
                except ValueError:
                    print("Please enter a valid number.")

            elif choice == 'B':
                return
            else:
                print("Invalid choice.")

        except Error as e:
            print(f"Error managing follow requests: {e}")

    def respond_to_follow_request(self, follower_id, response):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Get the request details
            query = "SELECT * FROM Followers WHERE FollowerID = %s"
            cursor.execute(query, (follower_id,))
            request = cursor.fetchone()

            if not request:
                print("Follow request not found.")
                return

            # Update the follow request
            update_query = "UPDATE Followers SET Status = %s, RespondedAt = NOW() WHERE FollowerID = %s"
            cursor.execute(update_query, (response, follower_id))

            # Get the follower's username
            user_query = "SELECT Username FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (request['FollowerUserID'],))
            follower = cursor.fetchone()

            if response == 'accepted':
                # Create notification for the follower
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], request['FollowerUserID'], 'accepted your follow request',
                                'follow_accept'))

                print(f"You have accepted {follower['Username']}'s follow request.")
            else:
                # Create notification for the follower
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], request['FollowerUserID'], 'rejected your follow request',
                                'follow_reject'))

                print(f"You have rejected {follower['Username']}'s follow request.")

            self.connection.commit()

        except Error as e:
            print(f"Error responding to follow request: {e}")
            self.connection.rollback()

    def view_user_profile(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.*, up.AvatarURL, up.Website, up.Location, up.About 
            FROM Users u 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID 
            WHERE u.UserID = %s
            """
            cursor.execute(query, (user_id,))
            profile = cursor.fetchone()

            if not profile:
                print("User not found.")
                return

            print(f"\n=== {profile['Name']}'s PROFILE ===")
            print(f"Name: {profile['Name']}")
            print(f"Username: {profile['Username']}")
            print(f"Bio: {profile['Bio']}")
            print(f"Location: {profile['Location']}")
            print(f"Website: {profile['Website']}")
            print(f"About: {profile['About']}")
            print(f"Account Type: {'Private' if profile['IsPrivate'] == 'Y' else 'Public'}")

            # Check follow status
            follow_query = "SELECT Status FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
            cursor.execute(follow_query, (user_id, self.current_user['UserID']))
            follow_status = cursor.fetchone()

            if follow_status:
                if follow_status['Status'] == 'accepted':
                    print("You are following this user")
                elif follow_status['Status'] == 'pending':
                    print("You have sent a follow request to this user")
                elif follow_status['Status'] == 'rejected':
                    print("Your follow request was rejected by this user")
            else:
                print("You are not following this user")

        except Error as e:
            print(f"Error viewing user profile: {e}")

    def share_post(self, post_id):
        try:
            message = input("Enter a message to go with your share (optional): ")

            cursor = self.connection.cursor(dictionary=True)

            # Insert into Shares table
            share_query = "INSERT INTO Shares (PostID, UserID, Message) VALUES (%s, %s, %s)"
            cursor.execute(share_query, (post_id, self.current_user['UserID'], message))

            # Get post owner ID
            post_query = "SELECT UserID FROM Posts WHERE PostID = %s"
            cursor.execute(post_query, (post_id,))
            post_owner = cursor.fetchone()

            if post_owner and post_owner['UserID'] != self.current_user['UserID']:
                # Create notification for the post owner
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], post_owner['UserID'], 'shared your post', 'share'))

            self.connection.commit()
            print("Post shared successfully!")

        except Error as e:
            print(f"Error sharing post: {e}")
            self.connection.rollback()

    def search_user(self):
        try:
            search_term = input("Enter username to search: ")

            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.UserID, u.Username, u.Name, u.Bio, up.Location, up.AvatarURL, u.IsPrivate
            FROM Users u 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID 
            WHERE u.Username LIKE %s OR u.Name LIKE %s
            """
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (search_pattern, search_pattern))
            users = cursor.fetchall()

            print(f"\n=== SEARCH RESULTS ===")
            if users:
                print(f"Found {len(users)} user(s) matching your search:")
                for i, user in enumerate(users):
                    print(f"\n{i + 1}. {user['Name']} (@{user['Username']})")
                    print(f"   Bio: {user['Bio']}")
                    print(f"   Location: {user['Location']}")
                    print(f"   Account Type: {'Private' if user['IsPrivate'] == 'Y' else 'Public'}")

                    # Check follow status
                    follow_query = "SELECT Status FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
                    cursor.execute(follow_query, (user['UserID'], self.current_user['UserID']))
                    follow_status = cursor.fetchone()

                    if follow_status:
                        if follow_status['Status'] == 'accepted':
                            print("   You are following this user")
                        elif follow_status['Status'] == 'pending':
                            print("   You have sent a follow request to this user")
                        elif follow_status['Status'] == 'rejected':
                            print("   Your follow request was rejected by this user")
                    else:
                        print("   You are not following this user")

                print("\nOptions:")
                print("F - Send follow request")
                print("V - View user's profile")
                print("P - View user's posts")
                print("B - Back to dashboard")

                choice = input("Enter your choice: ").upper()

                if choice == 'F':
                    try:
                        user_num = int(input("Enter the number of the user you want to follow: "))
                        if 1 <= user_num <= len(users):
                            self.send_follow_request(users[user_num - 1]['UserID'])
                        else:
                            print("Invalid user number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'V':
                    try:
                        user_num = int(input("Enter the number of the user whose profile you want to view: "))
                        if 1 <= user_num <= len(users):
                            self.view_user_profile(users[user_num - 1]['UserID'])
                        else:
                            print("Invalid user number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'P':
                    try:
                        user_num = int(input("Enter the number of the user whose posts you want to view: "))
                        if 1 <= user_num <= len(users):
                            self.view_user_posts(users[user_num - 1]['UserID'])
                        else:
                            print("Invalid user number.")
                    except ValueError:
                        print("Please enter a valid number.")
                elif choice == 'B':
                    return
                else:
                    print("Invalid choice.")
            else:
                print("No users found matching your search.")

        except Error as e:
            print(f"Error searching users: {e}")

    def view_user_posts(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Get user info
            user_query = "SELECT Username, Name FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (user_id,))
            user = cursor.fetchone()

            if not user:
                print("User not found.")
                return

            # Get user's posts
            posts_query = """
            SELECT p.*, u.Username, u.Name 
            FROM Posts p 
            JOIN Users u ON p.UserID = u.UserID 
            WHERE p.UserID = %s
            ORDER BY p.CreatedAt DESC
            """
            cursor.execute(posts_query, (user_id,))
            posts = cursor.fetchall()

            print(f"\n=== {user['Name']}'s POSTS ===")
            if posts:
                for post in posts:
                    print(f"\n{post['Name']} (@{post['Username']}) - {post['CreatedAt']}")
                    print(f"Content: {post['Content']}")

                    # Show media if exists
                    media_query = "SELECT * FROM Media WHERE PostID = %s"
                    cursor.execute(media_query, (post['PostID'],))
                    media = cursor.fetchall()

                    for m in media:
                        print(f"Media: {m['MediaURL']} ({m['MediaType']})")

                    # Show likes and comments count
                    likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
                    cursor.execute(likes_query, (post['PostID'],))
                    likes = cursor.fetchone()['count']

                    comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
                    cursor.execute(comments_query, (post['PostID'],))
                    comments = cursor.fetchone()['count']

                    print(f"Likes: {likes} | Comments: {comments}")
                    print("---")
            else:
                print("This user hasn't posted anything yet.")

        except Error as e:
            print(f"Error viewing user posts: {e}")


if __name__ == "__main__":
    app = SocialMediaApp()
    if app.connect_to_database():
        app.main_menu()
        if app.connection and app.connection.is_connected():
            app.connection.close()
            print("Database connection closed.")