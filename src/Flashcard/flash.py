import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import random
import datetime
import re

class StudySession:
    def __init__(self, parent, set_name):
        self.parent = parent
        self.set_name = set_name
        
        # Study tracking
        self.current_cards = []
        self.known_cards = []
        self.practice_cards = []
        self.current_card_index = 0
        self.study_mode = 'front'
        
        # Create study window
        self.window = tk.Toplevel(parent)
        self.window.title(f'Study Session: {set_name}')
        self.window.geometry('600x500')
        
        # Card Display Frame
        self.card_frame = ttk.Frame(self.window)
        self.card_frame.pack(expand=True, fill=BOTH, padx=20, pady=20)
        
        # Card Label
        self.card_label = ttk.Label(self.card_frame, 
                                    text='Loading Cards...', 
                                    font=('-size', 18), 
                                    anchor='center', 
                                    wraplength=500)
        self.card_label.pack(expand=True, fill=BOTH, pady=20)
        
        # Button Frame
        self.button_frame = ttk.Frame(self.window)
        self.button_frame.pack(fill=X, padx=20, pady=10)
        
        # Study Buttons
        self.flip_btn = ttk.Button(self.button_frame, 
                                   text='Flip Card', 
                                   command=self._flip_card, 
                                   style='primary.TButton')
        self.flip_btn.pack(side=LEFT, expand=True, padx=5)
        
        self.know_btn = ttk.Button(self.button_frame, 
                                   text='Know It', 
                                   command=lambda: self._record_card_result(True), 
                                   style='success.TButton')
        self.know_btn.config(state=DISABLED)
        self.know_btn.pack(side=LEFT, expand=True, padx=5)
        
        self.practice_btn = ttk.Button(self.button_frame, 
                                       text='Need Practice', 
                                       command=lambda: self._record_card_result(False), 
                                       style='warning.TButton')
        self.practice_btn.config(state=DISABLED)
        self.practice_btn.pack(side=LEFT, expand=True, padx=5)
        
        # Protocol for window closing
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Initialize study session
        self._load_cards()

    def _on_closing(self):
        # If study is not complete, ask for confirmation
        if self.current_cards:
            if messagebox.askyesno("Quit Study", "Are you sure you want to end the study session?"):
                self._show_study_results()
                self.window.destroy()
        else:
            self.window.destroy()

    def _update_session_statistics(self, total_cards, known_cards, practice_cards):
        try:
            conn = sqlite3.connect('mindflow_flashcards.db')
            cursor = conn.cursor()
            
            # Find the set ID
            cursor.execute('SELECT id FROM flashcard_sets WHERE name = ?', (self.set_name,))
            set_id = cursor.fetchone()[0]
            
            # Insert study session statistics
            cursor.execute('''
                INSERT INTO study_sessions (
                    set_id, 
                    total_cards, 
                    known_cards, 
                    practice_cards, 
                    study_date
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                set_id, 
                total_cards, 
                known_cards, 
                practice_cards, 
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating session statistics: {e}")
    
    def _load_cards(self):
        try:
            # Fetch cards for the selected set
            conn = sqlite3.connect('mindflow_flashcards.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    flashcards.id, 
                    flashcards.word, 
                    flashcards.definition, 
                    flashcards.example 
                FROM flashcards 
                JOIN flashcard_sets ON flashcards.set_id = flashcard_sets.id
                WHERE flashcard_sets.name = ?
            ''', (self.set_name,))
            
            self.current_cards = cursor.fetchall()
            conn.close()
            
            if not self.current_cards:
                messagebox.showerror('Error', 'No cards in this set')
                self.window.destroy()
                return
            
            # Shuffle cards
            random.shuffle(self.current_cards)
            
            # Reset study state
            self.current_card_index = 0
            self.study_mode = 'front'
            self.known_cards = []
            self.practice_cards = []
            
            # Display first card
            self._display_current_card()
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load cards: {str(e)}')
            self.window.destroy()
    
    def _display_current_card(self):
        if not self.current_cards:
            self._show_study_results()
            return
        
        # Get current card
        current_card = self.current_cards[self.current_card_index]
        
        # Display front of card (word)
        self.card_label.config(text=current_card[1])
        self.study_mode = 'front'
        
        # Enable/disable buttons
        self.know_btn.config(state=DISABLED)
        self.practice_btn.config(state=DISABLED)
        self.flip_btn.config(state=NORMAL)
    
    def _flip_card(self):
        if not self.current_cards:
            return
        
        current_card = self.current_cards[self.current_card_index]
        
        if self.study_mode == 'front':
            # Show back of card (definition)
            display_text = current_card[2]
            if current_card[3]:  # If example exists
                display_text += f"\n\nExample: {current_card[3]}"
            
            self.card_label.config(text=display_text)
            self.study_mode = 'back'
            
            # Enable know and practice buttons
            self.know_btn.config(state=NORMAL)
            self.practice_btn.config(state=NORMAL)
            self.flip_btn.config(state=DISABLED)
        else:
            # Show front of card again
            self._display_current_card()
    
    def _record_card_result(self, known):
        if not self.current_cards:
            return
        
        try:
            # Get current card
            current_card = self.current_cards[self.current_card_index]
            
            # Track card based on result
            if known:
                self.known_cards.append(current_card)
            else:
                self.practice_cards.append(current_card)
            
            # Remove current card
            self.current_cards.pop(self.current_card_index)
            
            # Reset index if it's out of range
            if self.current_card_index >= len(self.current_cards):
                self.current_card_index = 0
            
            # Display next card or finish
            if self.current_cards:
                self._display_current_card()
            else:
                self._show_study_results()
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to record card result: {str(e)}')
    
    def _show_study_results(self):
        # Create results window
        results_window = tk.Toplevel(self.parent)
        results_window.title('Study Session Results')
        results_window.geometry('600x700')
        
        # Results Notebook
        notebook = ttk.Notebook(results_window)
        notebook.pack(expand=True, fill=BOTH, padx=10, pady=10)
        
        # Known Cards Tab
        known_frame = ttk.Frame(notebook)
        notebook.add(known_frame, text='Known Cards')
        
        known_list = tk.Listbox(known_frame, width=70, height=20, font=('-size', 12))
        known_list.pack(padx=10, pady=10, expand=True, fill=BOTH)
        
        for card in self.known_cards:
            known_list.insert(tk.END, f"Word: {card[1]} | Definition: {card[2]}")
        
        # Practice Cards Tab
        practice_frame = ttk.Frame(notebook)
        notebook.add(practice_frame, text='Cards Needing Practice')
        
        practice_list = tk.Listbox(practice_frame, width=70, height=20, font=('-size', 12))
        practice_list.pack(padx=10, pady=10, expand=True, fill=BOTH)
        
        for card in self.practice_cards:
            practice_list.insert(tk.END, f"Word: {card[1]} | Definition: {card[2]}")
        
        # Summary Statistics
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text='Summary')
        
        summary_text = tk.Text(summary_frame, wrap=tk.WORD, width=70, height=20, font=('-size', 12))
        summary_text.pack(padx=10, pady=10, expand=True, fill=BOTH)
        
        # Calculate and display comprehensive statistics
        total_cards = len(self.known_cards) + len(self.practice_cards)
        known_percent = (len(self.known_cards) / total_cards * 100) if total_cards > 0 else 0
        practice_percent = (len(self.practice_cards) / total_cards * 100) if total_cards > 0 else 0
        
        # Add more detailed metrics
        summary_text.insert(tk.END, f"Study Session Summary for Set: {self.set_name}\n\n")
        summary_text.insert(tk.END, f"Total Cards Studied: {total_cards}\n")
        summary_text.insert(tk.END, f"Known Cards: {len(self.known_cards)} ({known_percent:.2f}%)\n")
        summary_text.insert(tk.END, f"Cards Needing Practice: {len(self.practice_cards)} ({practice_percent:.2f}%)\n\n")
        
        # Performance Analysis
        if total_cards > 0:
            confidence_level = known_percent / 100
            if confidence_level < 0.5:
                performance_desc = "Needs significant improvement"
            elif confidence_level < 0.7:
                performance_desc = "Moderate understanding"
            elif confidence_level < 0.9:
                performance_desc = "Strong grasp"
            else:
                performance_desc = "Mastery level"
            
            summary_text.insert(tk.END, f"Performance Level: {performance_desc}\n")
            summary_text.insert(tk.END, f"Confidence Score: {confidence_level:.2%}\n")
        
        # Optional: Improvement Suggestions
        summary_text.insert(tk.END, "\nTips:\n")
        if practice_percent > 50:
            summary_text.insert(tk.END, "- Focus on reviewing cards in the practice list\n")
        if len(self.practice_cards) > 0:
            summary_text.insert(tk.END, "- Create additional study sessions for challenging cards\n")
        
        # Make text read-only
        summary_text.config(state=tk.DISABLED)
        
        # Optional: Database update for session statistics
        self._update_session_statistics(total_cards, len(self.known_cards), len(self.practice_cards))
        
        # Close button
        close_btn = ttk.Button(results_window, text='Close', 
                            command=results_window.destroy, 
                            style='secondary.TButton')
        close_btn.pack(pady=10)

class FlashcardManager:
    def __init__(self, root):
        self.root = root
        # self.pack(fill="both", expand=True)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True)
        
        # Database Connection
        self.conn = sqlite3.connect('mindflow_flashcards.db')
        self.create_tables()
        
        # Styling
        # self.style = ttk.Style(theme='darkly')
        
        # Current study state variables
        self.current_set_id = None
        self.current_cards = []
        self.current_card_index = 0
        self.study_mode = 'normal'
        
        # Cards temporarily stored before saving set
        self.temp_cards = []
        
        # Flag to track if set is created
        self.set_created = False
        self.current_set_name = None
        
        # Setup UI
        self.setup_ui()
        self._load_sets()
    
    def setup_ui(self):
        # Main notebook for different sections
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Create tabs
        self.create_set_tab = self._create_tab('Create Set')
        self.manage_sets_tab = self._create_tab('Manage Sets')
        self.study_mode_tab = self._create_tab('Study Mode')
        self.statistics_tab = self._create_tab('Statistics')
        
        # Setup each tab's content
        self._setup_create_set_tab()
        self._setup_manage_sets_tab()
        self._setup_study_mode_tab()
        self._setup_statistics_tab()
    
    def _create_tab(self, name):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=name)
        return tab
    
    def _setup_manage_sets_tab(self):
        # Treeview for set management
        self.sets_tree = ttk.Treeview(self.manage_sets_tab, 
            columns=('Name', 'Cards', 'Created', 'Tags'), show='headings')
        
        self.sets_tree.heading('Name', text='Set Name')
        self.sets_tree.heading('Cards', text='Total Cards')
        self.sets_tree.heading('Created', text='Created Date')
        self.sets_tree.heading('Tags', text='Tags')
        
        self.sets_tree.pack(padx=20, pady=10, fill=BOTH, expand=YES)
        
        # Refresh Sets Button
        ttk.Button(self.manage_sets_tab, text='Refresh Sets', 
                   command=self._load_sets, style='info.TButton').pack(pady=10)
    
    def _setup_study_mode_tab(self):
        # Main Study Session Frame
        study_frame = ttk.Frame(self.study_mode_tab)
        study_frame.pack(padx=20, pady=20, expand=True)
        
        # Title
        ttk.Label(study_frame, text='Flashcard Study Session', 
                  font=('-size', 18, '-weight', 'bold')).pack(pady=10)
        
        # Set Selection Label
        ttk.Label(study_frame, text='Select a Flashcard Set to Study', 
                  font=('-size', 14)).pack(pady=5)
        
        # Set Selection Dropdown
        self.study_set_var = tk.StringVar()
        self.study_sets_combo = ttk.Combobox(study_frame, 
                                             textvariable=self.study_set_var, 
                                             state='readonly', 
                                             width=40)
        self.study_sets_combo.pack(pady=10)
        
        # Start Study Button
        self.start_study_btn = ttk.Button(study_frame, 
                                          text='Start Study Session', 
                                          command=self._start_study, 
                                          style='success.TButton')
        self.start_study_btn.pack(pady=10)
    
    def _setup_statistics_tab(self):
        # Statistics Display
        stats_frame = ttk.Frame(self.statistics_tab)
        stats_frame.pack(padx=20, pady=10, fill=BOTH, expand=YES)
        
        # Total Sets Label
        self.total_sets_label = ttk.Label(stats_frame, text='Total Sets: 0', font=('-size', 14))
        self.total_sets_label.pack(pady=5)
        
        # Total Cards Label
        self.total_cards_label = ttk.Label(stats_frame, text='Total Cards: 0', font=('-size', 14))
        self.total_cards_label.pack(pady=5)
        
        # Refresh Statistics Button
        ttk.Button(stats_frame, text='Refresh Statistics', 
                   command=self._update_statistics, style='secondary.TButton').pack(pady=10)
    
    def _load_sets(self):
        try:
            cursor = self.conn.cursor()
            
            # Fetch all sets
            cursor.execute('''
                SELECT id, name, total_cards, created_at, tags 
                FROM flashcard_sets
            ''')
            sets = cursor.fetchall()
            
            # Update Manage Sets Treeview
            for item in self.sets_tree.get_children():
                self.sets_tree.delete(item)
            
            for set_data in sets:
                self.sets_tree.insert('', END, values=(
                    set_data[1],  # Name
                    set_data[2],  # Total Cards
                    datetime.datetime.strptime(set_data[3], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),  # Created Date
                    set_data[4] or 'No Tags'  # Tags
                ))
            
            # Update Study Sets Combobox
            set_names = [set_data[1] for set_data in sets]
            self.study_sets_combo['values'] = set_names
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load sets: {str(e)}')
    
    # Placeholder methods for unimplemented functionality
    def _start_study(self):
        # Get selected set name
        set_name = self.study_set_var.get()
        
        if not set_name:
            messagebox.showerror('Error', 'Please select a set to study')
            return
        
        # Open study session window
        StudySession(self.root, set_name)
    
    def _display_current_card(self):
        if not self.current_cards:
            messagebox.showinfo('Finished', 'You have completed studying this set!')
            return
        
        # Get current card
        current_card = self.current_cards[self.current_card_index]
        
        # Display front of card (word)
        self.card_label.config(text=current_card[1], font=('-size', 20))
        
        # Update study mode
        self.study_mode = 'front'
    
    def _flip_card(self):
        if not self.current_cards:
            return
        
        current_card = self.current_cards[self.current_card_index]
        
        if self.study_mode == 'front':
            # Show back of card (definition)
            display_text = current_card[2]
            if current_card[3]:  # If example exists
                display_text += f"\n\nExample: {current_card[3]}"
            
            self.card_label.config(text=display_text, font=('-size', 16))
            self.study_mode = 'back'
        else:
            # Show front of card again
            self._display_current_card()
    
    def _record_card_result(self, known):
        if not self.current_cards:
            return
        
        try:
            # Update card statistics in database
            current_card = self.current_cards[self.current_card_index]
            cursor = self.conn.cursor()
            
            # Update review statistics
            cursor.execute('''
                UPDATE flashcards 
                SET 
                    review_count = review_count + 1,
                    correct_count = correct_count + ?,
                    last_reviewed = CURRENT_TIMESTAMP,
                    mastery_score = (
                        (mastery_score * review_count + ?) / (review_count + 1)
                    )
                WHERE id = ?
            ''', (1 if known else 0, 1.0 if known else 0.0, current_card[0]))
            
            self.conn.commit()
            
            # Remove current card if known or reshuffle if not
            if known:
                self.current_cards.pop(self.current_card_index)
            else:
                # Move card to end of the list
                card = self.current_cards.pop(self.current_card_index)
                self.current_cards.append(card)
            
            # Reset index if it's out of range
            if self.current_card_index >= len(self.current_cards):
                self.current_card_index = 0
            
            # Display next card or finish
            if self.current_cards:
                self._display_current_card()
            else:
                self.card_label.config(text='Congratulations! You\'ve mastered all cards in this set!', 
                                       font=('-size', 16))
                messagebox.showinfo('Study Complete', 'You\'ve finished studying this set!')
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to record card result: {str(e)}')
    
    def _update_statistics(self):
        try:
            cursor = self.conn.cursor()
            
            # Count total sets
            cursor.execute('SELECT COUNT(*) FROM flashcard_sets')
            total_sets = cursor.fetchone()[0]
            
            # Count total cards
            cursor.execute('SELECT COUNT(*) FROM flashcards')
            total_cards = cursor.fetchone()[0]
            
            # Update labels
            self.total_sets_label.config(text=f'Total Sets: {total_sets}')
            self.total_cards_label.config(text=f'Total Cards: {total_cards}')
        
        except Exception as e:
            messagebox.showerror('Error', f'Failed to update statistics: {str(e)}')
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Existing table creation code...
        
        # Add study sessions tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_id INTEGER NOT NULL,
                total_cards INTEGER NOT NULL,
                known_cards INTEGER NOT NULL,
                practice_cards INTEGER NOT NULL,
                study_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (set_id) REFERENCES flashcard_sets(id) ON DELETE CASCADE
            )
        ''')
        
        self.conn.commit()
    
    def _setup_create_set_tab(self):
        # Set Name Section
        ttk.Label(self.create_set_tab, text='Create New Flashcard Set', 
                font=('-size', 16, '-weight', 'bold')).pack(pady=10)
        
        set_frame = ttk.Frame(self.create_set_tab)
        set_frame.pack(padx=20, pady=10, fill=X)
        
        # Set Name Entry
        ttk.Label(set_frame, text='Set Name:').pack(side=LEFT, padx=5)
        self.set_name_var = tk.StringVar()
        set_name_entry = ttk.Entry(set_frame, textvariable=self.set_name_var, width=40)
        set_name_entry.pack(side=LEFT, padx=5)
        
        # Tags Entry
        ttk.Label(set_frame, text='Tags:').pack(side=LEFT, padx=5)
        self.set_tags_var = tk.StringVar()
        set_tags_entry = ttk.Entry(set_frame, textvariable=self.set_tags_var, width=20)
        set_tags_entry.pack(side=LEFT, padx=5)
        
        # Create Set Button
        create_set_btn = ttk.Button(set_frame, text='Create Set', 
                                    command=self._create_set, 
                                    style='success.TButton')
        create_set_btn.pack(side=LEFT, padx=5)
        
        # Card Entry Section 
        self.card_frame = ttk.LabelFrame(self.create_set_tab, text='Add Flashcards')
        self.card_frame.pack(padx=20, pady=10, fill=X)
        
        # Word/Term Entry
        ttk.Label(self.card_frame, text='Word/Term:').pack()
        self.word_var = tk.StringVar()
        word_entry = ttk.Entry(self.card_frame, textvariable=self.word_var, width=50)
        word_entry.pack(pady=5)
        
        # Definition Entry
        ttk.Label(self.card_frame, text='Definition/Explanation:').pack()
        self.definition_var = tk.StringVar()
        definition_entry = ttk.Entry(self.card_frame, textvariable=self.definition_var, width=50)
        definition_entry.pack(pady=5)
        
        # Example Entry (Optional)
        ttk.Label(self.card_frame, text='Example (Optional):').pack()
        self.example_var = tk.StringVar()
        example_entry = ttk.Entry(self.card_frame, textvariable=self.example_var, width=50)
        example_entry.pack(pady=5)
        
        # Buttons
        self.card_button_frame = ttk.Frame(self.create_set_tab)
        self.card_button_frame.pack(pady=10)
        
        ttk.Button(self.card_button_frame, text='Add Card', 
                command=self._add_card, 
                style='primary.TButton').pack(side=LEFT, padx=5)
        
        # Temporary Cards List
        self.temp_cards_list = tk.Listbox(self.create_set_tab, width=70, height=10)
        self.temp_cards_list.pack(pady=10)
        
        # Final Save Set Button
        self.save_set_btn = ttk.Button(self.create_set_tab, text='Finalize Set', 
                                    command=self._finalize_set, 
                                    style='success.TButton')
        self.save_set_btn.pack(pady=10)

    def _create_set(self):
        set_name = self.set_name_var.get().strip()
        tags = self.set_tags_var.get().strip()
        
        if not set_name:
            messagebox.showerror('Error', 'Set name is required!')
            return
        
        # Check if set name already exists
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM flashcard_sets WHERE name = ?', (set_name,))
        if cursor.fetchone():
            messagebox.showerror('Error', f'A set named "{set_name}" already exists!')
            return
        
        # Reset temporary storage
        self.temp_cards = []
        
        # Show/hide appropriate UI elements
        self.card_frame.pack(padx=20, pady=10, fill=X)
        self.card_button_frame.pack(pady=10)
        
        # Reset and show temporary cards list
        self.temp_cards_list.delete(0, tk.END)
        self.temp_cards_list.pack(pady=10)
        
        # Show finalize set button
        self.save_set_btn.pack(pady=10)
        
        # Set created flag and store set name
        self.set_created = True
        self.current_set_name = set_name
        self.current_set_tags = tags
        
        messagebox.showinfo('Success', f'Set "{set_name}" created. Now add cards.')

    def _add_card(self):
        if not self.set_created:
            messagebox.showerror('Error', 'Create a set first!')
            return
        
        word = self.word_var.get().strip()
        definition = self.definition_var.get().strip()
        example = self.example_var.get().strip()
        
        if not word or not definition:
            messagebox.showerror('Error', 'Word and Definition are required!')
            return
        
        # Add card to temporary storage
        card_entry = f"Word: {word} | Definition: {definition}"
        if example:
            card_entry += f" | Example: {example}"
        
        self.temp_cards.append({
            'word': word,
            'definition': definition,
            'example': example
        })
        
        # Add to listbox
        self.temp_cards_list.insert(tk.END, card_entry)
        
        # Clear input fields
        self.word_var.set('')
        self.definition_var.set('')
        self.example_var.set('')
        
        messagebox.showinfo('Success', f'Card added: {word}')
    
    def _finalize_set(self):
        if not self.temp_cards:
            messagebox.showerror('Error', 'Add at least one card before finalizing!')
            return
        
        try:
            # Start a transaction
            cursor = self.conn.cursor()
            
            # Insert the set
            cursor.execute('''
                INSERT INTO flashcard_sets (name, tags, total_cards) 
                VALUES (?, ?, ?)
            ''', (self.current_set_name, self.current_set_tags, len(self.temp_cards)))
            
            # Get the set ID
            set_id = cursor.lastrowid
            
            # Insert cards for this set
            for card in self.temp_cards:
                cursor.execute('''
                    INSERT INTO flashcards (set_id, word, definition, example) 
                    VALUES (?, ?, ?, ?)
                ''', (
                    set_id, 
                    card['word'], 
                    card['definition'], 
                    card['example'] or None
                ))
            
            # Commit the transaction
            self.conn.commit()
            
            # Show success message
            messagebox.showinfo('Success', 
                                f'Set "{self.current_set_name}" created with {len(self.temp_cards)} cards!')
            
            # Reset UI and variables
            self.set_name_var.set('')
            self.set_tags_var.set('')
            self.temp_cards = []
            self.temp_cards_list.delete(0, tk.END)
            self.card_frame.pack_forget()
            self.card_button_frame.pack_forget()
            self.temp_cards_list.pack_forget()
            self.save_set_btn.pack_forget()
            
            # Reset flags
            self.set_created = False
            self.current_set_name = None
            
            # Refresh sets in other tabs
            self._load_sets()
        
        except Exception as e:
            # Handle any unexpected errors
            messagebox.showerror('Error', f'Failed to save set: {str(e)}')
            self.conn.rollback()
    
    def run(self):
        self.root.mainloop()

def main(parent=None):
    if parent is None:
        root = ttk.Window()
        app = FlashcardManager(root)
        app.run()
    else:
        # If a parent is provided, create the FlashcardManager with the parent window
        app = FlashcardManager(parent)