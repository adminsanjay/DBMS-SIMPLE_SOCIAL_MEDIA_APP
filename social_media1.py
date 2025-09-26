import mysql.connector
from mysql.connector import Error
import bcrypt
import streamlit as st
from datetime import datetime, date
import time

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
                password='your_password'
            )

            if self.connection.is_connected():
                return True

        except Error as e:
            st.error(f"❌ Error while connecting to MySQL: {e}")
            return False

    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def login(self, username, password):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "SELECT * FROM Users WHERE Username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if user and self.check_password(password, user['PasswordHash']):
                self.current_user = user
                st.session_state.current_user = user
                st.success(f"🎉 Login successful! Welcome {user['Name']}!")
                return True
            else:
                st.error("❌ Invalid username or password.")
                return False

        except Error as e:
            st.error(f"❌ Error during login: {e}")
            return False

    def signup(self, username, email, password, name, gender, dob, bio, is_private):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Check if username already exists
            check_query = "SELECT * FROM Users WHERE Username = %s OR Email = %s"
            cursor.execute(check_query, (username, email))
            if cursor.fetchone():
                st.error("❌ Username or email already exists!")
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
            st.success("✅ Account created successfully! You can now login.")
            return True

        except Error as e:
            st.error(f"❌ Error during signup: {e}")
            self.connection.rollback()
            return False

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

            st.subheader("👤 Your Profile")

            col1, col2 = st.columns([1, 2])

            with col1:
                if profile['AvatarURL']:
                    st.image(profile['AvatarURL'], width=150)
                else:
                    st.image("https://via.placeholder.com/150", width=150)

                st.write(f"**Account Type:** {'🔒 Private' if profile['IsPrivate'] == 'Y' else '🌐 Public'}")

            with col2:
                st.write(f"**Name:** {profile['Name']}")
                st.write(f"**Username:** @{profile['Username']}")
                st.write(f"**Email:** {profile['Email']}")
                st.write(f"**Gender:** {profile['Gender']}")
                st.write(f"**Date of Birth:** {profile['DOB']}")
                st.write(f"**Bio:** {profile['Bio']}")
                st.write(f"**Location:** {profile['Location'] or 'Not specified'}")
                st.write(f"**Website:** {profile['Website'] or 'Not specified'}")
                st.write(f"**About:** {profile['About'] or 'Not specified'}")

            # Show followers and following count
            followers_query = "SELECT COUNT(*) as count FROM Followers WHERE UserID = %s AND Status = 'accepted'"
            cursor.execute(followers_query, (self.current_user['UserID'],))
            followers = cursor.fetchone()['count']

            following_query = "SELECT COUNT(*) as count FROM Followers WHERE FollowerUserID = %s AND Status = 'accepted'"
            cursor.execute(following_query, (self.current_user['UserID'],))
            following = cursor.fetchone()['count']

            pending_query = "SELECT COUNT(*) as count FROM Followers WHERE UserID = %s AND Status = 'pending'"
            cursor.execute(pending_query, (self.current_user['UserID'],))
            pending = cursor.fetchone()['count']

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Followers", followers)
            with col2:
                st.metric("Following", following)
            with col3:
                st.metric("Pending Requests", pending)

        except Error as e:
            st.error(f"❌ Error viewing profile: {e}")

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

            st.subheader("📝 My Posts")

            if not posts:
                st.info("You haven't created any posts yet.")
                return

            for post in posts:
                with st.container():
                    col1, col2 = st.columns([1, 20])
                    with col1:
                        st.image("https://via.placeholder.com/40", width=40)
                    with col2:
                        st.write(f"**{post['Name']}** (@{post['Username']})")
                        st.caption(f"Posted on {post['CreatedAt']}")

                    st.write(post['Content'])

                    # Show media if exists
                    media_query = "SELECT * FROM Media WHERE PostID = %s"
                    cursor.execute(media_query, (post['PostID'],))
                    media = cursor.fetchall()

                    for m in media:
                        if m['MediaType'] == 'image':
                            st.image(m['MediaURL'], width=300)
                        elif m['MediaType'] == 'video':
                            st.video(m['MediaURL'])

                    # Show likes and comments count
                    likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
                    cursor.execute(likes_query, (post['PostID'],))
                    likes = cursor.fetchone()['count']

                    comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
                    cursor.execute(comments_query, (post['PostID'],))
                    comments = cursor.fetchone()['count']

                    shares_query = "SELECT COUNT(*) as count FROM Shares WHERE PostID = %s"
                    cursor.execute(shares_query, (post['PostID'],))
                    shares = cursor.fetchone()['count']

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.button(f"❤️ {likes}", key=f"like_{post['PostID']}", disabled=True)
                    with col2:
                        if st.button(f"💬 {comments}", key=f"view_comments_{post['PostID']}"):
                            st.session_state[f"show_comments_{post['PostID']}"] = True
                    with col3:
                        st.button(f"🔁 {shares}", key=f"share_{post['PostID']}", disabled=True)
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{post['PostID']}"):
                            self.delete_post(post['PostID'])
                            st.rerun()

                    # Show comments if expanded
                    if st.session_state.get(f"show_comments_{post['PostID']}", False):
                        self.view_post_comments_with_edit(post['PostID'])
                        if st.button("Hide Comments", key=f"hide_comments_{post['PostID']}"):
                            st.session_state[f"show_comments_{post['PostID']}"] = False
                            st.rerun()

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing posts: {e}")

    def create_post(self):
        st.subheader("📝 Create New Post")

        with st.form("create_post_form"):
            content = st.text_area("What's on your mind?", placeholder="Share your thoughts...")
            media_url = st.text_input("Media URL (optional)", placeholder="https://example.com/image.jpg")
            media_type = st.selectbox("Media Type", ["", "image", "video"]) if media_url else None

            submitted = st.form_submit_button("Create Post")

            if submitted:
                if not content.strip():
                    st.error("❌ Post content cannot be empty!")
                    return

                try:
                    cursor = self.connection.cursor(dictionary=True)
                    post_query = "INSERT INTO Posts (UserID, Content) VALUES (%s, %s)"
                    cursor.execute(post_query, (self.current_user['UserID'], content))
                    post_id = cursor.lastrowid

                    if media_url and media_type:
                        media_query = "INSERT INTO Media (PostID, MediaURL, MediaType) VALUES (%s, %s, %s)"
                        cursor.execute(media_query, (post_id, media_url, media_type))

                    self.connection.commit()
                    st.success("✅ Post created successfully!")
                    time.sleep(1)
                    st.rerun()

                except Error as e:
                    st.error(f"❌ Error creating post: {e}")

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

            st.subheader("🔔 Notifications")

            if not notifications:
                st.info("No notifications")
                return

            for notification in notifications:
                with st.container():
                    col1, col2 = st.columns([1, 20])
                    with col1:
                        st.image("https://via.placeholder.com/40", width=40)
                    with col2:
                        st.write(
                            f"**{notification['SenderName']}** (@{notification['SenderUsername']}) {notification['Message']}")
                        st.caption(f"Time: {notification['CreatedAt']}")

                    # For follow requests, show options to accept/reject
                    if notification['Type'] == 'follow_request':
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Accept", key=f"accept_{notification['NotificationID']}"):
                                self.respond_to_follow_request(notification['SenderID'], 'accepted')
                                st.rerun()
                        with col2:
                            if st.button("❌ Reject", key=f"reject_{notification['NotificationID']}"):
                                self.respond_to_follow_request(notification['SenderID'], 'rejected')
                                st.rerun()

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing notifications: {e}")

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

            st.subheader("🌐 Browse Posts")

            if not posts:
                st.info("No posts available to browse. Be the first to create a post!")
                return

            # Use session state to track current post index
            if 'current_post_index' not in st.session_state:
                st.session_state.current_post_index = 0

            current_index = st.session_state.current_post_index
            post = posts[current_index]

            # Display current post
            with st.container():
                col1, col2 = st.columns([1, 20])
                with col1:
                    st.image("https://via.placeholder.com/40", width=40)
                with col2:
                    st.write(f"**{post['Name']}** (@{post['Username']})")
                    st.caption(f"Posted on {post['CreatedAt']}")

                st.write(post['Content'])

                # Show media if exists
                media_query = "SELECT * FROM Media WHERE PostID = %s"
                cursor.execute(media_query, (post['PostID'],))
                media = cursor.fetchall()

                for m in media:
                    if m['MediaType'] == 'image':
                        st.image(m['MediaURL'], width=300)
                    elif m['MediaType'] == 'video':
                        st.video(m['MediaURL'])

                # Show engagement metrics
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

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    like_text = "❤️ Unlike" if user_liked else "🤍 Like"
                    if st.button(f"{like_text} {likes}", key=f"like_{post['PostID']}"):
                        self.toggle_like(post['PostID'])
                        st.rerun()
                with col2:
                    if st.button(f"💬 {comments}", key=f"comment_btn_{post['PostID']}"):
                        st.session_state[f"show_comment_{post['PostID']}"] = True
                with col3:
                    if st.button(f"🔁 {shares}", key=f"share_{post['PostID']}"):
                        self.share_post_ui(post['PostID'])
                with col4:
                    if st.button("👤 Follow", key=f"follow_{post['PostID']}"):
                        self.send_follow_request(post['UserID'])
                        st.rerun()

                # Comment section
                if st.session_state.get(f"show_comment_{post['PostID']}", False):
                    with st.form(f"comment_form_{post['PostID']}"):
                        comment_text = st.text_area("Add a comment")
                        if st.form_submit_button("Post Comment"):
                            if comment_text.strip():
                                self.add_comment(post['PostID'], comment_text)
                                st.rerun()

                # View comments section
                if st.button("📋 View Comments", key=f"view_comments_{post['PostID']}"):
                    self.view_post_comments_with_edit(post['PostID'])

                # Navigation
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("⬅️ Previous") and current_index > 0:
                        st.session_state.current_post_index -= 1
                        st.rerun()
                with col2:
                    st.write(f"Post {current_index + 1} of {len(posts)}")
                with col3:
                    if st.button("Next ➡️") and current_index < len(posts) - 1:
                        st.session_state.current_post_index += 1
                        st.rerun()

        except Error as e:
            st.error(f"❌ Error browsing posts: {e}")

    def toggle_like(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            check_query = "SELECT * FROM Likes WHERE PostID = %s AND UserID = %s"
            cursor.execute(check_query, (post_id, self.current_user['UserID']))
            existing_like = cursor.fetchone()

            if existing_like:
                delete_query = "DELETE FROM Likes WHERE PostID = %s AND UserID = %s"
                cursor.execute(delete_query, (post_id, self.current_user['UserID']))
                st.success("💔 Post unliked!")
            else:
                insert_query = "INSERT INTO Likes (PostID, UserID) VALUES (%s, %s)"
                cursor.execute(insert_query, (post_id, self.current_user['UserID']))

                # Create notification
                post_query = "SELECT UserID FROM Posts WHERE PostID = %s"
                cursor.execute(post_query, (post_id,))
                post_owner = cursor.fetchone()

                if post_owner and post_owner['UserID'] != self.current_user['UserID']:
                    notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                    cursor.execute(notif_query,
                                   (self.current_user['UserID'], post_owner['UserID'], 'liked your post', 'like'))

                st.success("❤️ Post liked!")

            self.connection.commit()

        except Error as e:
            st.error(f"❌ Error toggling like: {e}")

    def add_comment(self, post_id, comment_text):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = "INSERT INTO Comments (PostID, UserID, TextComment) VALUES (%s, %s, %s)"
            cursor.execute(query, (post_id, self.current_user['UserID'], comment_text))

            # Create notification
            post_query = "SELECT UserID FROM Posts WHERE PostID = %s"
            cursor.execute(post_query, (post_id,))
            post_owner = cursor.fetchone()

            if post_owner and post_owner['UserID'] != self.current_user['UserID']:
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], post_owner['UserID'], 'commented on your post', 'comment'))

            self.connection.commit()
            st.success("✅ Comment added successfully!")

        except Error as e:
            st.error(f"❌ Error adding comment: {e}")

    def view_post_comments_with_edit(self, post_id):
        """Enhanced comments view with editing functionality"""
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

            st.subheader("💬 Comments")

            if not comments:
                st.info("No comments for this post.")
                return

            for comment in comments:
                with st.container():
                    col1, col2, col3 = st.columns([1, 4, 1])
                    with col1:
                        st.image("https://via.placeholder.com/30", width=30)
                    with col2:
                        st.write(f"**{comment['Name']}** (@{comment['Username']})")

                        # Check if we're in edit mode for this comment
                        if st.session_state.get(f"editing_comment_{comment['CommentID']}", False):
                            with st.form(f"edit_comment_form_{comment['CommentID']}"):
                                edited_text = st.text_area("Edit comment", value=comment['TextComment'],
                                                           key=f"edit_text_{comment['CommentID']}")
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.form_submit_button("💾 Save"):
                                        self.update_comment(comment['CommentID'], edited_text)
                                        st.session_state[f"editing_comment_{comment['CommentID']}"] = False
                                        st.rerun()
                                with col2:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state[f"editing_comment_{comment['CommentID']}"] = False
                                        st.rerun()
                        else:
                            st.write(comment['TextComment'])
                            st.caption(f"Posted on {comment['CreatedAt']}")

                    with col3:
                        # Allow users to edit/delete their own comments
                        if comment['UserID'] == self.current_user['UserID']:
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("✏️", key=f"edit_{comment['CommentID']}"):
                                    st.session_state[f"editing_comment_{comment['CommentID']}"] = True
                                    st.rerun()
                            with col2:
                                if st.button("🗑️", key=f"delete_comment_{comment['CommentID']}"):
                                    self.delete_comment(comment['CommentID'])
                                    st.rerun()

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing comments: {e}")

    def update_comment(self, comment_id, new_text):
        """Update an existing comment"""
        try:
            if not new_text.strip():
                st.error("❌ Comment cannot be empty!")
                return

            cursor = self.connection.cursor(dictionary=True)
            update_query = "UPDATE Comments SET TextComment = %s WHERE CommentID = %s AND UserID = %s"
            cursor.execute(update_query, (new_text, comment_id, self.current_user['UserID']))
            self.connection.commit()
            st.success("✅ Comment updated successfully!")
        except Error as e:
            st.error(f"❌ Error updating comment: {e}")

    def delete_comment(self, comment_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            delete_query = "DELETE FROM Comments WHERE CommentID = %s AND UserID = %s"
            cursor.execute(delete_query, (comment_id, self.current_user['UserID']))
            self.connection.commit()
            st.success("✅ Comment deleted successfully!")
        except Error as e:
            st.error(f"❌ Error deleting comment: {e}")

    def share_post_ui(self, post_id):
        with st.form(f"share_form_{post_id}"):
            message = st.text_area("Add a message to your share (optional)")
            if st.form_submit_button("Share Post"):
                self.share_post(post_id, message)
                st.rerun()

    def share_post(self, post_id, message):
        try:
            cursor = self.connection.cursor(dictionary=True)
            share_query = "INSERT INTO Shares (PostID, UserID, Message) VALUES (%s, %s, %s)"
            cursor.execute(share_query, (post_id, self.current_user['UserID'], message))

            # Create notification
            post_query = "SELECT UserID FROM Posts WHERE PostID = %s"
            cursor.execute(post_query, (post_id,))
            post_owner = cursor.fetchone()

            if post_owner and post_owner['UserID'] != self.current_user['UserID']:
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], post_owner['UserID'], 'shared your post', 'share'))

            self.connection.commit()
            st.success("✅ Post shared successfully!")

        except Error as e:
            st.error(f"❌ Error sharing post: {e}")

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

            st.subheader("❤️ Posts You've Liked")

            if not posts:
                st.info("You haven't liked any posts yet.")
                return

            for post in posts:
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 1])
                    with col1:
                        st.image("https://via.placeholder.com/40", width=40)
                    with col2:
                        st.write(f"**{post['Name']}** (@{post['Username']})")
                        st.caption(f"Posted on {post['CreatedAt']}")
                        st.write(post['Content'][:100] + "..." if len(post['Content']) > 100 else post['Content'])

                        # Show comments for this post
                        if st.button("💬 View Comments", key=f"view_comments_liked_{post['PostID']}"):
                            self.view_post_comments_with_edit(post['PostID'])

                    with col3:
                        if st.button("💔 Unlike", key=f"unlike_{post['PostID']}"):
                            self.unlike_post(post['PostID'])
                            st.rerun()
                        if st.button("👀 View Full", key=f"view_{post['PostID']}"):
                            st.session_state.view_post_id = post['PostID']
                            st.session_state.current_page = "view_single_post"

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing liked posts: {e}")

    def unlike_post(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            delete_query = "DELETE FROM Likes WHERE PostID = %s AND UserID = %s"
            cursor.execute(delete_query, (post_id, self.current_user['UserID']))
            self.connection.commit()
            st.success("💔 Post unliked!")
        except Error as e:
            st.error(f"❌ Error unliking post: {e}")

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
                st.error("Post not found.")
                return

            st.subheader("📄 Post Details")

            col1, col2 = st.columns([1, 20])
            with col1:
                st.image("https://via.placeholder.com/40", width=40)
            with col2:
                st.write(f"**{post['Name']}** (@{post['Username']})")
                st.caption(f"Posted on {post['CreatedAt']}")

            st.write(post['Content'])

            # Show media if exists
            media_query = "SELECT * FROM Media WHERE PostID = %s"
            cursor.execute(media_query, (post_id,))
            media = cursor.fetchall()

            for m in media:
                if m['MediaType'] == 'image':
                    st.image(m['MediaURL'], width=300)
                elif m['MediaType'] == 'video':
                    st.video(m['MediaURL'])

            # Show engagement metrics
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

            col1, col2 = st.columns(2)
            with col1:
                like_text = "❤️ Unlike" if user_liked else "🤍 Like"
                if st.button(f"{like_text} {likes}", key=f"like_{post_id}"):
                    self.toggle_like(post_id)
                    st.rerun()
            with col2:
                if st.button(f"💬 View Comments ({comments})", key=f"view_comments_{post_id}"):
                    self.view_post_comments_with_edit(post_id)

            # Add comment functionality
            with st.form(f"add_comment_form_{post_id}"):
                comment_text = st.text_area("Add a comment")
                if st.form_submit_button("Post Comment"):
                    if comment_text.strip():
                        self.add_comment(post_id, comment_text)
                        st.rerun()

            if st.button("← Back to Liked Posts", key="back_to_liked"):
                st.session_state.current_page = "liked_posts"
                st.rerun()

        except Error as e:
            st.error(f"❌ Error viewing post: {e}")

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

            st.subheader("✏️ Edit Profile")

            with st.form("edit_profile_form"):
                col1, col2 = st.columns(2)

                with col1:
                    new_name = st.text_input("Name", value=profile['Name'])
                    new_username = st.text_input("Username", value=profile['Username'])
                    new_email = st.text_input("Email", value=profile['Email'])
                    new_bio = st.text_area("Bio", value=profile['Bio'])

                with col2:
                    new_gender = st.selectbox("Gender", ["M", "F", "O"],
                                              index=["M", "F", "O"].index(profile['Gender']) if profile['Gender'] in [
                                                  "M", "F", "O"] else 0)

                    # Fix for DOB - handle both string and date objects
                    if isinstance(profile['DOB'], date):
                        current_dob = profile['DOB']
                    else:
                        # If it's a string, parse it
                        try:
                            current_dob = datetime.strptime(str(profile['DOB']), '%Y-%m-%d').date()
                        except:
                            current_dob = date.today()

                    new_dob = st.date_input("Date of Birth", value=current_dob)
                    new_location = st.text_input("Location", value=profile['Location'] or "")
                    new_website = st.text_input("Website", value=profile['Website'] or "")

                new_about = st.text_area("About", value=profile['About'] or "")
                new_avatar = st.text_input("Avatar URL", value=profile['AvatarURL'] or "")
                new_privacy = st.selectbox("Privacy Setting", ["Public", "Private"],
                                           index=1 if profile['IsPrivate'] == 'Y' else 0)

                if st.form_submit_button("Update Profile"):
                    try:
                        # Update Users table
                        user_update_query = """
                        UPDATE Users 
                        SET Name = %s, Username = %s, Email = %s, Bio = %s, Gender = %s, DOB = %s, IsPrivate = %s
                        WHERE UserID = %s
                        """
                        cursor.execute(user_update_query, (
                            new_name, new_username, new_email, new_bio, new_gender,
                            new_dob, 'Y' if new_privacy == 'Private' else 'N',
                            self.current_user['UserID']
                        ))

                        # Update UserProfile table
                        profile_update_query = """
                        UPDATE UserProfile 
                        SET AvatarURL = %s, Website = %s, Location = %s, About = %s
                        WHERE UserID = %s
                        """
                        cursor.execute(profile_update_query, (
                            new_avatar, new_website, new_location, new_about,
                            self.current_user['UserID']
                        ))

                        self.connection.commit()
                        st.success("✅ Profile updated successfully!")
                        # Update current user session
                        st.session_state.current_user['Name'] = new_name
                        st.session_state.current_user['Username'] = new_username
                        st.session_state.current_user['Email'] = new_email
                        time.sleep(1)
                        st.rerun()

                    except Error as e:
                        st.error(f"❌ Error updating profile: {e}")
                        self.connection.rollback()

        except Error as e:
            st.error(f"❌ Error loading profile: {e}")

    def change_password(self):
        st.subheader("🔒 Change Password")

        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Change Password"):
                if not all([current_password, new_password, confirm_password]):
                    st.error("❌ Please fill in all fields!")
                    return

                if new_password != confirm_password:
                    st.error("❌ New passwords do not match!")
                    return

                try:
                    cursor = self.connection.cursor(dictionary=True)
                    query = "SELECT PasswordHash FROM Users WHERE UserID = %s"
                    cursor.execute(query, (self.current_user['UserID'],))
                    user = cursor.fetchone()

                    if not self.check_password(current_password, user['PasswordHash']):
                        st.error("❌ Current password is incorrect!")
                        return

                    # Hash new password
                    hashed_password = self.hash_password(new_password)

                    # Update password
                    update_query = "UPDATE Users SET PasswordHash = %s WHERE UserID = %s"
                    cursor.execute(update_query, (hashed_password, self.current_user['UserID']))
                    self.connection.commit()

                    st.success("✅ Password changed successfully!")

                except Error as e:
                    st.error(f"❌ Error changing password: {e}")
                    self.connection.rollback()

    def view_followers(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.UserID, u.Username, u.Name, u.Bio, up.AvatarURL
            FROM Users u 
            JOIN Followers f ON u.UserID = f.FollowerUserID 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID
            WHERE f.UserID = %s AND f.Status = 'accepted'
            """
            cursor.execute(query, (self.current_user['UserID'],))
            followers = cursor.fetchall()

            st.subheader("👥 Your Followers")

            if not followers:
                st.info("You don't have any followers yet.")
                return

            for follower in followers:
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 2])
                    with col1:
                        st.image(follower['AvatarURL'] or "https://via.placeholder.com/50", width=50)
                    with col2:
                        st.write(f"**{follower['Name']}** (@{follower['Username']})")
                        st.write(follower['Bio'] or "No bio")
                    with col3:
                        if st.button("👤 View Profile", key=f"view_follower_{follower['UserID']}"):
                            st.session_state.view_user_id = follower['UserID']
                            st.session_state.current_page = "view_user_profile"
                        if st.button("🚫 Unfollow", key=f"unfollow_{follower['UserID']}"):
                            self.unfollow_user(follower['UserID'])
                            st.rerun()

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing followers: {e}")

    def view_following(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT u.UserID, u.Username, u.Name, u.Bio, up.AvatarURL
            FROM Users u 
            JOIN Followers f ON u.UserID = f.UserID 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID
            WHERE f.FollowerUserID = %s AND f.Status = 'accepted'
            """
            cursor.execute(query, (self.current_user['UserID'],))
            following = cursor.fetchall()

            st.subheader("👥 Users You Follow")

            if not following:
                st.info("You're not following anyone yet.")
                return

            for user in following:
                with st.container():
                    col1, col2, col3 = st.columns([1, 3, 2])
                    with col1:
                        st.image(user['AvatarURL'] or "https://via.placeholder.com/50", width=50)
                    with col2:
                        st.write(f"**{user['Name']}** (@{user['Username']})")
                        st.write(user['Bio'] or "No bio")
                    with col3:
                        if st.button("👤 View Profile", key=f"view_following_{user['UserID']}"):
                            st.session_state.view_user_id = user['UserID']
                            st.session_state.current_page = "view_user_profile"
                        if st.button("🚫 Unfollow", key=f"unfollow_following_{user['UserID']}"):
                            self.unfollow_user(user['UserID'])
                            st.rerun()

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing following: {e}")

    def unfollow_user(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Check if user exists
            user_query = "SELECT Username FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (user_id,))
            user = cursor.fetchone()

            if not user:
                st.error("❌ User not found.")
                return

            # Check if actually following
            follow_query = "SELECT * FROM Followers WHERE UserID = %s AND FollowerUserID = %s AND Status = 'accepted'"
            cursor.execute(follow_query, (user_id, self.current_user['UserID']))
            existing_follow = cursor.fetchone()

            if not existing_follow:
                st.error(f"❌ You are not following {user['Username']}.")
                return

            # Unfollow the user
            delete_query = "DELETE FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
            cursor.execute(delete_query, (user_id, self.current_user['UserID']))

            self.connection.commit()
            st.success(f"✅ You have unfollowed {user['Username']}.")

        except Error as e:
            st.error(f"❌ Error unfollowing user: {e}")
            self.connection.rollback()

    def manage_follow_requests(self):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT f.*, u.Username, u.Name, up.AvatarURL
            FROM Followers f 
            JOIN Users u ON f.FollowerUserID = u.UserID 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID
            WHERE f.UserID = %s AND f.Status = 'pending'
            """
            cursor.execute(query, (self.current_user['UserID'],))
            requests = cursor.fetchall()

            st.subheader("📨 Pending Follow Requests")

            if not requests:
                st.info("You don't have any pending follow requests.")
                return

            for request in requests:
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                    with col1:
                        st.image(request['AvatarURL'] or "https://via.placeholder.com/50", width=50)
                    with col2:
                        st.write(f"**{request['Name']}** (@{request['Username']})")
                        st.caption(f"Requested on {request['RequestedAt']}")
                    with col3:
                        if st.button("✅ Accept", key=f"accept_{request['FollowerID']}"):
                            self.respond_to_follow_request(request['FollowerID'], 'accepted')
                            st.rerun()
                    with col4:
                        if st.button("❌ Reject", key=f"reject_{request['FollowerID']}"):
                            self.respond_to_follow_request(request['FollowerID'], 'rejected')
                            st.rerun()

                    st.divider()

        except Error as e:
            st.error(f"❌ Error managing follow requests: {e}")

    def respond_to_follow_request(self, follower_id, response):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Update the follow request
            update_query = "UPDATE Followers SET Status = %s, RespondedAt = NOW() WHERE FollowerID = %s"
            cursor.execute(update_query, (response, follower_id))

            # Get the follower's username
            user_query = "SELECT Username FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (follower_id,))
            follower = cursor.fetchone()

            if response == 'accepted':
                # Create notification for the follower
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], follower_id, 'accepted your follow request',
                                'follow_accept'))
                st.success(f"✅ You have accepted {follower['Username']}'s follow request.")
            else:
                # Create notification for the follower
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], follower_id, 'rejected your follow request',
                                'follow_reject'))
                st.success(f"✅ You have rejected {follower['Username']}'s follow request.")

            self.connection.commit()

        except Error as e:
            st.error(f"❌ Error responding to follow request: {e}")
            self.connection.rollback()

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

            st.subheader("🔁 Posts That Have Been Shared")

            if not posts_with_shares:
                st.info("Your posts haven't been shared yet.")
                return

            for post in posts_with_shares:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Post:** {post['Content'][:100]}...")
                        st.write(f"**Share Count:** {post['share_count']}")
                    with col2:
                        if st.button("👀 View Shares", key=f"view_shares_{post['PostID']}"):
                            self.view_post_shares_details(post['PostID'])

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing post shares: {e}")

    def view_post_shares_details(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
            SELECT s.*, u.Username, u.Name, up.AvatarURL
            FROM Shares s 
            JOIN Users u ON s.UserID = u.UserID 
            LEFT JOIN UserProfile up ON u.UserID = up.UserID
            WHERE s.PostID = %s 
            ORDER BY s.SharedAt DESC
            """
            cursor.execute(query, (post_id,))
            shares = cursor.fetchall()

            st.subheader("👥 Who Shared This Post")

            if not shares:
                st.info("This post hasn't been shared yet.")
                return

            for share in shares:
                with st.container():
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.image(share['AvatarURL'] or "https://via.placeholder.com/40", width=40)
                    with col2:
                        st.write(f"**{share['Name']}** (@{share['Username']})")
                        if share['Message']:
                            st.write(f"*\"{share['Message']}\"*")
                        st.caption(f"Shared on {share['SharedAt']}")

                    st.divider()

        except Error as e:
            st.error(f"❌ Error viewing post shares details: {e}")

    def delete_account(self):
        st.subheader("🗑️ Delete Account")
        st.warning("⚠️ This action cannot be undone! All your data will be permanently deleted.")

        with st.form("delete_account_form"):
            password = st.text_input("Enter your password to confirm", type="password")
            confirm_text = st.text_input("Type 'DELETE MY ACCOUNT' to confirm")

            if st.form_submit_button("Delete Account"):
                if confirm_text != "DELETE MY ACCOUNT":
                    st.error("❌ Please type exactly 'DELETE MY ACCOUNT' to confirm.")
                    return

                try:
                    # Verify password
                    cursor = self.connection.cursor(dictionary=True)
                    query = "SELECT PasswordHash FROM Users WHERE UserID = %s"
                    cursor.execute(query, (self.current_user['UserID'],))
                    user = cursor.fetchone()

                    if not self.check_password(password, user['PasswordHash']):
                        st.error("❌ Incorrect password. Account deletion cancelled.")
                        return

                    # Delete user (cascades to all related tables due to ON DELETE CASCADE)
                    delete_query = "DELETE FROM Users WHERE UserID = %s"
                    cursor.execute(delete_query, (self.current_user['UserID'],))
                    self.connection.commit()

                    st.success("✅ Your account has been deleted successfully.")
                    st.session_state.current_user = None
                    st.session_state.current_page = "login"
                    time.sleep(2)
                    st.rerun()

                except Error as e:
                    st.error(f"❌ Error deleting account: {e}")
                    self.connection.rollback()

    def search_user(self):
        st.subheader("🔍 Search Users")

        search_term = st.text_input("Enter username or name to search")

        if search_term:
            try:
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

                if users:
                    st.write(f"Found {len(users)} user(s):")

                    for user in users:
                        with st.container():
                            col1, col2, col3 = st.columns([1, 3, 2])
                            with col1:
                                st.image(user['AvatarURL'] or "https://via.placeholder.com/50", width=50)
                            with col2:
                                st.write(f"**{user['Name']}** (@{user['Username']})")
                                st.write(user['Bio'] or "No bio")
                                st.write(f"📍 {user['Location'] or 'No location'}")
                                st.write(f"**Account Type:** {'🔒 Private' if user['IsPrivate'] == 'Y' else '🌐 Public'}")
                            with col3:
                                # Check follow status
                                follow_query = "SELECT Status FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
                                cursor.execute(follow_query, (user['UserID'], self.current_user['UserID']))
                                follow_status = cursor.fetchone()

                                if follow_status:
                                    if follow_status['Status'] == 'accepted':
                                        st.button("✅ Following", key=f"follow_{user['UserID']}", disabled=True)
                                    elif follow_status['Status'] == 'pending':
                                        st.button("⏳ Requested", key=f"pending_{user['UserID']}", disabled=True)
                                    else:
                                        if st.button("👤 Follow", key=f"follow_{user['UserID']}"):
                                            self.send_follow_request(user['UserID'])
                                            st.rerun()
                                else:
                                    if st.button("👤 Follow", key=f"follow_{user['UserID']}"):
                                        self.send_follow_request(user['UserID'])
                                        st.rerun()

                                if st.button("👀 View Profile", key=f"view_{user['UserID']}"):
                                    st.session_state.view_user_id = user['UserID']
                                    st.session_state.current_page = "view_user_profile"

                                if st.button("📝 View Posts", key=f"posts_{user['UserID']}"):
                                    self.view_user_posts(user['UserID'])

                            st.divider()
                else:
                    st.info("No users found matching your search.")

            except Error as e:
                st.error(f"❌ Error searching users: {e}")

    def send_follow_request(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            user_query = "SELECT Username, Name, IsPrivate FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (user_id,))
            user = cursor.fetchone()

            if not user:
                st.error("❌ User not found.")
                return

            if user_id == self.current_user['UserID']:
                st.error("❌ You cannot follow yourself.")
                return

            # Check if already following or request pending
            follow_query = "SELECT * FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
            cursor.execute(follow_query, (user_id, self.current_user['UserID']))
            existing_follow = cursor.fetchone()

            if existing_follow:
                if existing_follow['Status'] == 'accepted':
                    st.info(f"✅ You are already following {user['Username']}.")
                elif existing_follow['Status'] == 'pending':
                    st.info(f"⏳ You have already sent a follow request to {user['Username']}.")
                elif existing_follow['Status'] == 'rejected':
                    st.info(f"❌ Your previous follow request to {user['Username']} was rejected.")
                return

            # For public accounts, follow directly
            if user['IsPrivate'] == 'N':
                insert_query = "INSERT INTO Followers (UserID, FollowerUserID, Status, RespondedAt) VALUES (%s, %s, 'accepted', NOW())"
                cursor.execute(insert_query, (user_id, self.current_user['UserID']))

                # Create notification
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], user_id, 'started following you', 'follow_accept'))

                st.success(f"✅ You are now following {user['Username']}.")
            else:
                # For private accounts, send follow request
                insert_query = "INSERT INTO Followers (UserID, FollowerUserID, Status) VALUES (%s, %s, 'pending')"
                cursor.execute(insert_query, (user_id, self.current_user['UserID']))

                # Create notification
                notif_query = "INSERT INTO Notifications (SenderID, ReceiverID, Message, Type) VALUES (%s, %s, %s, %s)"
                cursor.execute(notif_query,
                               (self.current_user['UserID'], user_id, 'sent you a follow request', 'follow_request'))

                st.success(f"✅ Follow request sent to {user['Username']}. Waiting for approval.")

            self.connection.commit()

        except Error as e:
            st.error(f"❌ Error sending follow request: {e}")
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
                st.error("User not found.")
                return

            st.subheader(f"👤 {profile['Name']}'s Profile")

            col1, col2 = st.columns([1, 2])

            with col1:
                if profile['AvatarURL']:
                    st.image(profile['AvatarURL'], width=150)
                else:
                    st.image("https://via.placeholder.com/150", width=150)

                st.write(f"**Account Type:** {'🔒 Private' if profile['IsPrivate'] == 'Y' else '🌐 Public'}")

            with col2:
                st.write(f"**Name:** {profile['Name']}")
                st.write(f"**Username:** @{profile['Username']}")
                st.write(f"**Bio:** {profile['Bio']}")
                st.write(f"**Location:** {profile['Location'] or 'Not specified'}")
                st.write(f"**Website:** {profile['Website'] or 'Not specified'}")
                st.write(f"**About:** {profile['About'] or 'Not specified'}")

            # Check follow status
            follow_query = "SELECT Status FROM Followers WHERE UserID = %s AND FollowerUserID = %s"
            cursor.execute(follow_query, (user_id, self.current_user['UserID']))
            follow_status = cursor.fetchone()

            if follow_status:
                if follow_status['Status'] == 'accepted':
                    st.info("✅ You are following this user")
                elif follow_status['Status'] == 'pending':
                    st.info("⏳ You have sent a follow request to this user")
                elif follow_status['Status'] == 'rejected':
                    st.info("❌ Your follow request was rejected by this user")
            else:
                st.info("🔍 You are not following this user")

            if st.button("📝 View User's Posts"):
                self.view_user_posts(user_id)

            if st.button("← Back to Search"):
                st.session_state.current_page = "search"
                st.rerun()

        except Error as e:
            st.error(f"❌ Error viewing user profile: {e}")

    def view_user_posts(self, user_id):
        try:
            cursor = self.connection.cursor(dictionary=True)

            # Get user info
            user_query = "SELECT Username, Name FROM Users WHERE UserID = %s"
            cursor.execute(user_query, (user_id,))
            user = cursor.fetchone()

            if not user:
                st.error("User not found.")
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

            st.subheader(f"📝 {user['Name']}'s Posts")

            if not posts:
                st.info("This user hasn't posted anything yet.")
                return

            for post in posts:
                with st.container():
                    col1, col2 = st.columns([1, 20])
                    with col1:
                        st.image("https://via.placeholder.com/40", width=40)
                    with col2:
                        st.write(f"**{post['Name']}** (@{post['Username']})")
                        st.caption(f"Posted on {post['CreatedAt']}")

                    st.write(post['Content'])

                    # Show media if exists
                    media_query = "SELECT * FROM Media WHERE PostID = %s"
                    cursor.execute(media_query, (post['PostID'],))
                    media = cursor.fetchall()

                    for m in media:
                        if m['MediaType'] == 'image':
                            st.image(m['MediaURL'], width=300)
                        elif m['MediaType'] == 'video':
                            st.video(m['MediaURL'])

                    # Show likes and comments count
                    likes_query = "SELECT COUNT(*) as count FROM Likes WHERE PostID = %s"
                    cursor.execute(likes_query, (post['PostID'],))
                    likes = cursor.fetchone()['count']

                    comments_query = "SELECT COUNT(*) as count FROM Comments WHERE PostID = %s"
                    cursor.execute(comments_query, (post['PostID'],))
                    comments = cursor.fetchone()['count']

                    col1, col2 = st.columns(2)
                    with col1:
                        st.button(f"❤️ {likes}", key=f"like_{post['PostID']}", disabled=True)
                    with col2:
                        if st.button(f"💬 {comments}", key=f"view_comments_{post['PostID']}"):
                            self.view_post_comments_with_edit(post['PostID'])

                    st.divider()

            if st.button("← Back to Profile"):
                st.session_state.current_page = "view_user_profile"
                st.rerun()

        except Error as e:
            st.error(f"❌ Error viewing user posts: {e}")

    def delete_post(self, post_id):
        try:
            cursor = self.connection.cursor(dictionary=True)
            delete_query = "DELETE FROM Posts WHERE PostID = %s AND UserID = %s"
            cursor.execute(delete_query, (post_id, self.current_user['UserID']))
            self.connection.commit()
            st.success("✅ Post deleted successfully!")
        except Error as e:
            st.error(f"❌ Error deleting post: {e}")


# Streamlit UI
def main():
    st.set_page_config(
        page_title="DISCUSS BOND MEME SHARE",
        page_icon="🌐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize session state
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"

    # Initialize app
    if 'app' not in st.session_state:
        st.session_state.app = SocialMediaApp()
        st.session_state.app.connect_to_database()

    app = st.session_state.app

    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1DA1F2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">🌐 DISCUSS BOND MEME SHARE</h1>', unsafe_allow_html=True)

    # Main content based on login status and current page
    if st.session_state.current_user is None:
        show_login_signup(app)
    else:
        show_dashboard(app)


def show_login_signup(app):
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        st.subheader("Login to Your Account")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login")

            if login_btn:
                if username and password:
                    if app.login(username, password):
                        st.session_state.current_page = "dashboard"
                        st.rerun()
                else:
                    st.error("❌ Please fill in all fields")

    with tab2:
        st.subheader("Create New Account")
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Choose a username")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
            with col2:
                name = st.text_input("Full Name")
                gender = st.selectbox("Gender", ["", "M", "F", "O"])
                dob = st.date_input("Date of Birth", min_value=datetime(1900, 1, 1))
                is_private = st.selectbox("Account Type", ["Public", "Private"]) == "Private"

            bio = st.text_area("Bio")

            signup_btn = st.form_submit_button("Create Account")

            if signup_btn:
                if password != confirm_password:
                    st.error("❌ Passwords do not match!")
                elif not all([username, email, password, name, gender, dob]):
                    st.error("❌ Please fill in all required fields!")
                else:
                    if app.signup(username, email, password, name, gender, dob.strftime('%Y-%m-%d'), bio,
                                  'Y' if is_private else 'N'):
                        st.rerun()


def show_dashboard(app):
    # Sidebar navigation
    with st.sidebar:
        st.header(f"👋 Welcome, {app.current_user['Name']}!")
        st.divider()

        # Navigation options
        nav_options = {
            "dashboard": "📊 Dashboard",
            "profile": "👤 My Profile",
            "edit_profile": "✏️ Edit Profile",
            "posts": "📝 My Posts",
            "create_post": "➕ Create Post",
            "liked_posts": "❤️ Liked Posts",
            "notifications": "🔔 Notifications",
            "browse": "🌐 Browse Posts",
            "search": "🔍 Search Users",
            "followers": "👥 Followers",
            "following": "👥 Following",
            "follow_requests": "📨 Follow Requests",
            "post_shares": "🔁 Post Shares",
            "change_password": "🔒 Change Password",
            "delete_account": "🗑️ Delete Account",
            "logout": "🚪 Logout"
        }

        for page_key, page_label in nav_options.items():
            if st.button(page_label, key=page_key, use_container_width=True):
                st.session_state.current_page = page_key
                st.rerun()

        st.divider()
        st.write(f"**Username:** @{app.current_user['Username']}")
        st.write(f"**Email:** {app.current_user['Email']}")

    # Main content area
    if st.session_state.current_page == "dashboard":
        show_dashboard_home(app)
    elif st.session_state.current_page == "profile":
        app.view_profile()
    elif st.session_state.current_page == "edit_profile":
        app.edit_profile()
    elif st.session_state.current_page == "posts":
        app.view_my_posts()
    elif st.session_state.current_page == "create_post":
        app.create_post()
    elif st.session_state.current_page == "liked_posts":
        app.view_liked_posts()
    elif st.session_state.current_page == "notifications":
        app.view_notifications()
    elif st.session_state.current_page == "browse":
        app.browse_posts()
    elif st.session_state.current_page == "search":
        app.search_user()
    elif st.session_state.current_page == "followers":
        app.view_followers()
    elif st.session_state.current_page == "following":
        app.view_following()
    elif st.session_state.current_page == "follow_requests":
        app.manage_follow_requests()
    elif st.session_state.current_page == "post_shares":
        app.view_post_shares()
    elif st.session_state.current_page == "change_password":
        app.change_password()
    elif st.session_state.current_page == "delete_account":
        app.delete_account()
    elif st.session_state.current_page == "view_single_post":
        app.view_single_post(st.session_state.get('view_post_id', 0))
    elif st.session_state.current_page == "view_user_profile":
        app.view_user_profile(st.session_state.get('view_user_id', 0))
    elif st.session_state.current_page == "logout":
        st.session_state.current_user = None
        st.session_state.current_page = "login"
        st.rerun()


def show_dashboard_home(app):
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📊 Dashboard Overview")

        try:
            cursor = app.connection.cursor(dictionary=True)

            # Get user stats
            posts_query = "SELECT COUNT(*) as count FROM Posts WHERE UserID = %s"
            cursor.execute(posts_query, (app.current_user['UserID'],))
            posts_count = cursor.fetchone()['count']

            followers_query = "SELECT COUNT(*) as count FROM Followers WHERE UserID = %s AND Status = 'accepted'"
            cursor.execute(followers_query, (app.current_user['UserID'],))
            followers_count = cursor.fetchone()['count']

            following_query = "SELECT COUNT(*) as count FROM Followers WHERE FollowerUserID = %s AND Status = 'accepted'"
            cursor.execute(following_query, (app.current_user['UserID'],))
            following_count = cursor.fetchone()['count']

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("My Posts", posts_count)
            with col2:
                st.metric("Followers", followers_count)
            with col3:
                st.metric("Following", following_count)

        except Error as e:
            st.error(f"❌ Error loading dashboard: {e}")

    with col2:
        st.subheader("Quick Actions")
        if st.button("📝 Create New Post", use_container_width=True):
            st.session_state.current_page = "create_post"
            st.rerun()
        if st.button("🌐 Browse Posts", use_container_width=True):
            st.session_state.current_page = "browse"
            st.rerun()
        if st.button("🔍 Search Users", use_container_width=True):
            st.session_state.current_page = "search"
            st.rerun()
        if st.button("❤️ View Liked Posts", use_container_width=True):
            st.session_state.current_page = "liked_posts"
            st.rerun()


if __name__ == "__main__":
    main()
