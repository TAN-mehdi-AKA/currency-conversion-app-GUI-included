

########### make sure you are using python version 3.11 

# =============================================================================
# SECTION 1: IMPORTS & CONFIG
# =============================================================================
import threading                      
import wx                             
from requests import get              

base_url = "https://api.freecurrencyapi.com/"                          
api_key = "fca_live_xcVLuMVbJFgFAZZWEnsJbQxPlaqGKi13icokmNog"         


# =============================================================================
# SECTION 2: LOGIC (your functions - no GUI code in here)
# =============================================================================

def get_currencies():
    endpoint = f"v1/currencies?apikey={api_key}"
    url = base_url + endpoint
    data = get(url, timeout=10).json()      

    data = data.get('data', {})

    data = list(data.items())
    data.sort()

    return data


def exchange_rate(currency1, currency2):
    endpoint = f"v1/latest?apikey={api_key}&currencies=&base_currency={currency1}"
    url = base_url + endpoint
    data = get(url, timeout=10).json()       

    data = data.get('data', {})

    data = list(data.items())
    data.sort()

    rate = None                             
    for curr in data:
        if curr[0] == currency2:
            rate = curr[1]
            currency = curr[0]
            
            print(f"{currency1}'s rate to convert to {currency2} is => {currency}={rate}")
        else:
            continue
    return rate


def convert(currency1, currency2, amount):
    rate = exchange_rate(currency1, currency2)
    if rate is None:
        return None                        

    try:
        amount = float(amount)
    except ValueError:                       
        return None                      

    converted_result = amount * rate

    print(f"{currency1} to {currency2} = {converted_result}")
    return converted_result


# =============================================================================
# SECTION 3: THEME  [STYLE]
# Change a colour here and the whole app follows.
# =============================================================================

WHITE = wx.Colour(255, 255, 255)
BG = wx.Colour(10, 14, 30)              # window background (deep navy)
CARD = wx.Colour(22, 28, 52)            # card surfaces
CARD_ALT = wx.Colour(26, 33, 60)        # alternate rows in lists
FIELD = wx.Colour(13, 18, 40)           # inputs / dropdown buttons
BORDER = wx.Colour(45, 55, 95)          # idle borders
HIGHLIGHT = wx.Colour(52, 44, 120)      # selected list row
TEXT = wx.Colour(237, 241, 255)         # main text
MUTED = wx.Colour(140, 150, 185)        # secondary text
ACCENT = wx.Colour(124, 92, 255)        # violet
ACCENT2 = wx.Colour(34, 211, 238)       # cyan
SUCCESS = wx.Colour(52, 211, 153)
ERROR = wx.Colour(251, 113, 133)


def font(size, bold=False):
    """[STYLE] Builds a font (created lazily because fonts need the App to exist)."""
    info = wx.FontInfo(size)
    if bold:
        info.Bold()
    return wx.Font(info)


def mix(c1, c2, t):
    """[STYLE] Blends two colours (t=0 -> c1, t=1 -> c2). Used for hover effects."""
    return wx.Colour(int(c1.Red() + (c2.Red() - c1.Red()) * t),
                     int(c1.Green() + (c2.Green() - c1.Green()) * t),
                     int(c1.Blue() + (c2.Blue() - c1.Blue()) * t))


def elide(measure, text, max_width):
    """[STYLE] Shortens text with an ellipsis so it never overflows its box."""
    if measure(text) <= max_width:
        return text
    while text and measure(text + "…") > max_width:
        text = text[:-1]
    return text + "…"


# SECTION 4: CUSTOM WIDGETS  [STYLE]

class GradientHeader(wx.Panel):
    """The violet -> cyan banner at the top with the app title."""

    def __init__(self, parent):
        super().__init__(parent, size=wx.Size(-1, 96))
        self.SetMinSize(wx.Size(-1, 96))
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, lambda e: (self.Refresh(), e.Skip()))

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetClientSize()

        # gradient background
        gc.SetBrush(gc.CreateLinearGradientBrush(0, 0, w, h, ACCENT, mix(ACCENT2, ACCENT, 0.15)))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.DrawRectangle(0, 0, w, h)

        # soft decorative circles
        gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, 30)))
        gc.DrawEllipse(w - 150, -70, 230, 230)
        gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, 22)))
        gc.DrawEllipse(w - 290, 40, 130, 130)

        # coin badge with a currency symbol
        gc.SetBrush(wx.Brush(wx.Colour(255, 255, 255, 45)))
        gc.SetPen(wx.Pen(wx.Colour(255, 255, 255, 140), 2))
        gc.DrawEllipse(24, 24, 48, 48)
        gc.SetFont(font(18, True), WHITE)
        tw, th = gc.GetTextExtent("$")[:2]
        gc.DrawText("$", 24 + (48 - tw) / 2, 24 + (48 - th) / 2)

        # title + subtitle
        gc.SetFont(font(20, True), WHITE)
        gc.DrawText("Currency Converter", 88, 20)
        gc.SetFont(font(10), wx.Colour(255, 255, 255, 215))
        gc.DrawText("Live exchange rates, one click away", 90, 56)


class FlatButton(wx.Control):
    """A custom-drawn button. kind = 'primary' (gradient), 'tab' or 'ghost'."""

    def __init__(self, parent, label, kind="primary", size=(-1, 48), font_size=11):
        super().__init__(parent, size=wx.Size(*size), style=wx.BORDER_NONE)
        self.SetMinSize(wx.Size(*size))
        self.label, self.kind, self.font_size = label, kind, font_size
        self.hover = self.down = self.active = False
        self.enabled = True
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, lambda e: self.set_state(hover=True))
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda e: self.set_state(hover=False))
        self.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_up)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, lambda e: self.set_state(down=False))
        self.Bind(wx.EVT_SIZE, lambda e: (self.Refresh(), e.Skip()))

    # --- state helpers ---
    def set_state(self, hover=None, down=None):
        if hover is not None:
            self.hover = hover
        if down is not None:
            self.down = down
        self.Refresh()

    def set_active(self, active):       
        self.active = active
        self.Refresh()

    def set_enabled(self, enabled):     
        self.enabled = enabled
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND if enabled else wx.CURSOR_ARROW))
        self.Refresh()

    def set_label(self, label):
        self.label = label
        self.Refresh()

    # --- mouse ---
    def on_down(self, event):
        if not self.enabled:
            return
        self.set_state(down=True)
        if not self.HasCapture():
            self.CaptureMouse()

    def on_up(self, event):
        if self.HasCapture():
            self.ReleaseMouse()
        was_down = self.down
        self.set_state(down=False)
        w, h = self.GetClientSize()
        x, y = event.GetPosition()
        if was_down and self.enabled and 0 <= x <= w and 0 <= y <= h:
            click = wx.CommandEvent(wx.EVT_BUTTON.typeId, self.GetId())
            click.SetEventObject(self)
            self.GetEventHandler().ProcessEvent(click)

    # --- drawing ---
    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetClientSize()
        offset = 1 if self.down else 0
        radius = h / 2 if self.kind == "tab" else 12

        gc.SetPen(wx.TRANSPARENT_PEN)
        text_colour = WHITE

        if self.kind == "primary":
            if not self.enabled:
                gc.SetBrush(wx.Brush(BORDER))
                text_colour = MUTED
            else:
                c1 = mix(ACCENT, WHITE, 0.12) if self.hover else ACCENT
                c2 = mix(ACCENT2, WHITE, 0.12) if self.hover else ACCENT2
                gc.SetBrush(gc.CreateLinearGradientBrush(0, 0, w, 0, c1, c2))
        elif self.kind == "tab":
            if self.active:
                gc.SetBrush(gc.CreateLinearGradientBrush(0, 0, w, 0, ACCENT, mix(ACCENT, ACCENT2, 0.5)))
            else:
                gc.SetBrush(wx.Brush(CARD if self.hover else BG))
                text_colour = TEXT if self.hover else MUTED
        else:  # ghost
            gc.SetBrush(wx.Brush(mix(CARD, ACCENT, 0.25) if self.hover else CARD))
            gc.SetPen(wx.Pen(ACCENT if self.hover else BORDER, 1))

        gc.DrawRoundedRectangle(0.5, 0.5 + offset, w - 1, h - 1, radius)

        gc.SetFont(font(self.font_size, True), text_colour)
        tw, th = gc.GetTextExtent(self.label)[:2]
        gc.DrawText(self.label, (w - tw) / 2, (h - th) / 2 + offset)


class Card(wx.Panel):
    """A rounded surface. Add your widgets to `card.body` (a vertical sizer)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(CARD)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.body = wx.BoxSizer(wx.VERTICAL)
        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(self.body, 1, wx.EXPAND | wx.ALL, 20)
        self.SetSizer(outer)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, lambda e: (self.Refresh(), e.Skip()))

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetClientSize()
        gc.SetBrush(wx.Brush(CARD))
        gc.SetPen(wx.Pen(BORDER, 1))
        gc.DrawRoundedRectangle(0.5, 0.5, w - 1, h - 1, 18)


class Field(wx.Panel):
    """A rounded text input whose border glows when focused."""

    def __init__(self, parent, value="", hint=""):
        super().__init__(parent)
        self.focused = False
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetBackgroundColour(FIELD)

        self.text = wx.TextCtrl(self, value=value, style=wx.BORDER_NONE | wx.TE_PROCESS_ENTER)
        self.text.SetBackgroundColour(FIELD)
        self.text.SetForegroundColour(TEXT)
        self.text.SetFont(font(13))
        if hint:
            self.text.SetHint(hint)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.text, 1, wx.EXPAND | wx.ALL, 14)
        self.SetSizer(sizer)

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_SIZE, lambda e: (self.Refresh(), e.Skip()))
        self.Bind(wx.EVT_LEFT_DOWN, lambda e: self.text.SetFocus())
        self.text.Bind(wx.EVT_SET_FOCUS, lambda e: (self.set_focused(True), e.Skip()))
        self.text.Bind(wx.EVT_KILL_FOCUS, lambda e: (self.set_focused(False), e.Skip()))

    def set_focused(self, focused):
        self.focused = focused
        self.Refresh()

    def GetValue(self):
        return self.text.GetValue()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetClientSize()
        gc.SetBrush(wx.Brush(FIELD))
        gc.SetPen(wx.Pen(ACCENT2 if self.focused else BORDER, 2 if self.focused else 1))
        gc.DrawRoundedRectangle(1, 1, w - 2, h - 2, 12)


class CurrencyListBox(wx.VListBox):
    """A themed scrolling list: CODE   Name   Symbol (used in the picker and the Currencies tab)."""

    def __init__(self, parent, items=None):
        super().__init__(parent, style=wx.BORDER_NONE)
        self.SetBackgroundColour(CARD)
        self.items = []
        self.set_items(items or [])

    def set_items(self, items):
        self.items = list(items)          
        self.SetItemCount(len(self.items))
        self.Refresh()

    def get_code(self):
        index = self.GetSelection()
        return self.items[index][0] if index != wx.NOT_FOUND else None

    def OnMeasureItem(self, n):
        return 42

    def OnDrawBackground(self, dc, rect, n):
        if self.IsSelected(n):
            colour = HIGHLIGHT
        else:
            colour = CARD if n % 2 == 0 else CARD_ALT
        dc.SetBrush(wx.Brush(colour))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)

    def OnDrawItem(self, dc, rect, n):
        code, name, symbol = self.items[n]
        selected = self.IsSelected(n)

        dc.SetFont(font(11, True))
        dc.SetTextForeground(WHITE if selected else ACCENT2)
        dc.DrawText(code, rect.x + 16, rect.y + (rect.height - dc.GetTextExtent(code)[1]) // 2)

        dc.SetFont(font(10))
        dc.SetTextForeground(TEXT)
        name = elide(lambda t: dc.GetTextExtent(t)[0], name, rect.width - 170)
        dc.DrawText(name, rect.x + 84, rect.y + (rect.height - dc.GetTextExtent(name)[1]) // 2)

        if symbol:
            dc.SetTextForeground(MUTED)
            sw = dc.GetTextExtent(symbol)[0]
            dc.DrawText(symbol, rect.right - 16 - sw,
                        rect.y + (rect.height - dc.GetTextExtent(symbol)[1]) // 2)


class PickerDialog(wx.Dialog):
    """Pop-up with a search box + list so you can find any currency fast."""

    def __init__(self, parent, items, current=None):
        super().__init__(parent, title="Choose a currency", size=wx.Size(440, 560),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetBackgroundColour(BG)
        self.all_items = items
        self.chosen = None

        self.search = Field(self, hint="Search by code or name…")
        self.list = CurrencyListBox(self, items)
        hint = wx.StaticText(self, label="Double-click or press Enter to select")
        hint.SetForegroundColour(MUTED)
        hint.SetBackgroundColour(BG)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.search, 0, wx.EXPAND | wx.ALL, 16)
        sizer.Add(self.list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)
        sizer.Add(hint, 0, wx.ALL, 14)
        self.SetSizer(sizer)

        self.search.text.Bind(wx.EVT_TEXT, self.on_filter)
        self.search.text.Bind(wx.EVT_TEXT_ENTER, self.accept)
        self.list.Bind(wx.EVT_LISTBOX_DCLICK, self.accept)
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key)

        # pre-select the current currency
        for index, item in enumerate(items):
            if item[0] == current:
                self.list.SetSelection(index)
                self.list.ScrollToRow(index)
                break
        self.search.text.SetFocus()
        self.CentreOnParent()

    def on_filter(self, event):
        query = self.search.GetValue().strip().lower()
        shown = [i for i in self.all_items if query in i[0].lower() or query in i[1].lower()]
        self.list.set_items(shown)
        if shown:
            self.list.SetSelection(0)

    def on_key(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_CANCEL)
        elif key in (wx.WXK_DOWN, wx.WXK_UP):  
            count = self.list.GetItemCount()
            if count:
                step = 1 if key == wx.WXK_DOWN else -1
                current = self.list.GetSelection()
                new = 0 if current == wx.NOT_FOUND else max(0, min(count - 1, current + step))
                self.list.SetSelection(new)
                self.list.ScrollToRow(new)
        else:
            event.Skip()

    def accept(self, event):
        code = self.list.get_code()
        if code:
            self.chosen = code
            self.EndModal(wx.ID_OK)


class PickerButton(wx.Control):
    """Replaces the plain dropdown: shows the chosen currency, opens PickerDialog on click."""

    def __init__(self, parent):
        super().__init__(parent, size=wx.Size(-1, 62), style=wx.BORDER_NONE)
        self.SetMinSize(wx.Size(-1, 62))
        self.items = []           
        self.code = None
        self.hover = False
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ENTER_WINDOW, lambda e: self.set_hover(True))
        self.Bind(wx.EVT_LEAVE_WINDOW, lambda e: self.set_hover(False))
        self.Bind(wx.EVT_LEFT_UP, self.on_click)
        self.Bind(wx.EVT_SIZE, lambda e: (self.Refresh(), e.Skip()))

    def set_hover(self, hover):
        self.hover = hover
        self.Refresh()

    def set_items(self, items):
        self.items = items
        self.Refresh()

    def set_code(self, code):
        self.code = code
        self.Refresh()

    def get_code(self):
        return self.code

    def on_click(self, event):
        if not self.items:
            return
        dialog = PickerDialog(self.GetTopLevelParent(), self.items, self.code)
        if dialog.ShowModal() == wx.ID_OK:
            self.set_code(dialog.chosen)
        dialog.Destroy()

    def on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()
        gc = wx.GraphicsContext.Create(dc)
        w, h = self.GetClientSize()

        gc.SetBrush(wx.Brush(FIELD))
        gc.SetPen(wx.Pen(ACCENT if self.hover else BORDER, 1))
        gc.DrawRoundedRectangle(0.5, 0.5, w - 1, h - 1, 12)

        match = [i for i in self.items if i[0] == self.code]
        if match:
            code, name, _ = match[0]
        else:
            code, name = "…", "Loading currencies"

        gc.SetFont(font(14, True), ACCENT2)
        gc.DrawText(code, 16, 9)
        gc.SetFont(font(9), MUTED)
        measure = lambda t: gc.GetTextExtent(t)[0]
        gc.DrawText(elide(measure, name, w - 70), 16, 34)

        # dropdown arrow
        path = gc.CreatePath()
        path.MoveToPoint(w - 30, h / 2 - 3)
        path.AddLineToPoint(w - 20, h / 2 - 3)
        path.AddLineToPoint(w - 25, h / 2 + 4)
        path.CloseSubpath()
        gc.SetBrush(wx.Brush(MUTED))
        gc.SetPen(wx.TRANSPARENT_PEN)
        gc.FillPath(path)


def make_label(parent, text, size=9, bold=True, colour=MUTED):
    """[STYLE] Small themed text label. Takes its background from the parent."""
    label = wx.StaticText(parent, label=text)
    label.SetFont(font(size, bold))
    label.SetForegroundColour(colour)
    label.SetBackgroundColour(parent.GetBackgroundColour())
    return label


# =============================================================================
# SECTION 5: GUI HELPERS
# =============================================================================

def run_in_background(task, on_success, on_error):
    """[NEW] Runs `task()` in a separate thread so the window stays responsive
    during the network call. wx.CallAfter hands the result back to the GUI thread."""
    def worker():
        try:
            result = task()
        except Exception as error:
            wx.CallAfter(on_error, error)
        else:
            wx.CallAfter(on_success, result)

    threading.Thread(target=worker, daemon=True).start()


# =============================================================================
# SECTION 6: THE WINDOW (frame + layout + event handlers)
# =============================================================================

class MainFrame(wx.Frame):                                  
    def __init__(self):
        super().__init__(None, title="Currency Converter", size=wx.Size(600, 800))
        self.SetMinSize(wx.Size(540, 720))
        self.SetBackgroundColour(BG)

        self.currencies = []    
        self.codes = []         

        # ---- Frame skeleton ----
        root = wx.Panel(self)                               
        root.SetBackgroundColour(BG)

        self.header = GradientHeader(root)                 

        
        self.tab_names = ["Convert", "Exchange Rate", "Currencies"]
        self.tabs = [FlatButton(root, name, kind="tab", size=(-1, 40), font_size=10)
                     for name in self.tab_names]
        tab_row = wx.BoxSizer(wx.HORIZONTAL)
        for index, tab in enumerate(self.tabs):
            tab_row.Add(tab, 1, wx.EXPAND | wx.RIGHT, 8 if index < len(self.tabs) - 1 else 0)
            tab.Bind(wx.EVT_BUTTON, lambda e, i=index: self.show_tab(i))

        self.book = wx.Simplebook(root)                     
        self.book.SetBackgroundColour(BG)

        self.status = wx.StaticText(root, label="")          
        self.status.SetFont(font(9))
        self.status.SetBackgroundColour(BG)
        self.set_status("Loading currencies...")

        layout = wx.BoxSizer(wx.VERTICAL)
        layout.Add(self.header, 0, wx.EXPAND)
        layout.Add(tab_row, 0, wx.EXPAND | wx.ALL, 16)
        layout.Add(self.book, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 16)
        layout.Add(self.status, 0, wx.EXPAND | wx.ALL, 14)
        root.SetSizer(layout)

        # ---- GUI content (each tab is built in its own method) ----
        self.build_convert_tab()
        self.build_rate_tab()
        self.build_list_tab()
        self.show_tab(0)

        # ---- Load the currencies on startup (replaces `currencies = get_currencies()` in main()) ----
        run_in_background(get_currencies, self.on_currencies_loaded, self.on_load_error)

        root.Layout()
        self.Centre()

    # -------------------------------------------------------------------------
    # SMALL UI HELPERS
    # -------------------------------------------------------------------------

    def show_tab(self, index):
        """[STYLE] Switches page and highlights the active tab button."""
        self.book.ChangeSelection(index)
        for i, tab in enumerate(self.tabs):
            tab.set_active(i == index)

    def set_status(self, text, colour=MUTED):
        """[STYLE] Replaces SetStatusText: shows a coloured line at the bottom."""
        self.status.SetForegroundColour(colour)
        self.status.SetLabel(text)

    def make_page(self):
        """[STYLE] Creates an empty themed page inside the book."""
        page = wx.Panel(self.book)
        page.SetBackgroundColour(BG)
        self.book.AddPage(page, "")
        return page

    def make_result_card(self, page):
        """[STYLE] The big result box used by both the Convert and Rate tabs."""
        card = Card(page)
        big = wx.StaticText(card, label=" ", style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE)
        big.SetFont(font(20, True))
        big.SetForegroundColour(TEXT)
        big.SetBackgroundColour(CARD)
        big.SetMinSize(wx.Size(-1, 38))
        small = wx.StaticText(card, label=" ", style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE)
        small.SetFont(font(10))
        small.SetForegroundColour(MUTED)
        small.SetBackgroundColour(CARD)
        small.SetMinSize(wx.Size(-1, 22))
        card.body.Add(make_label(card, "RESULT"), 0, wx.BOTTOM, 6)
        card.body.Add(big, 0, wx.EXPAND)
        card.body.Add(small, 0, wx.EXPAND | wx.TOP, 4)
        return card, big, small

    def make_picker_row(self, card, left_text, right_text):
        """[STYLE] Two currency pickers with a swap button between them."""
        left_picker, right_picker = PickerButton(card), PickerButton(card)
        swap = FlatButton(card, "⇄", kind="ghost", size=(46, 46), font_size=14)

        left_col = wx.BoxSizer(wx.VERTICAL)
        left_col.Add(make_label(card, left_text), 0, wx.BOTTOM, 6)
        left_col.Add(left_picker, 0, wx.EXPAND)

        right_col = wx.BoxSizer(wx.VERTICAL)
        right_col.Add(make_label(card, right_text), 0, wx.BOTTOM, 6)
        right_col.Add(right_picker, 0, wx.EXPAND)

        swap_col = wx.BoxSizer(wx.VERTICAL)
        swap_col.AddStretchSpacer()
        swap_col.Add(swap, 0)
        swap_col.AddSpacer(8)

        row = wx.BoxSizer(wx.HORIZONTAL)
        row.Add(left_col, 1, wx.EXPAND)
        row.Add(swap_col, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        row.Add(right_col, 1, wx.EXPAND)

        swap.Bind(wx.EVT_BUTTON, lambda e: self.swap_pickers(left_picker, right_picker))
        return row, left_picker, right_picker

    def swap_pickers(self, first, second):
        """[STYLE] Swap button: exchanges the two selected currencies."""
        a, b = first.get_code(), second.get_code()
        first.set_code(b)
        second.set_code(a)

    # -------------------------------------------------------------------------
    # GUI CONTENT: building the tabs
    # -------------------------------------------------------------------------

    def build_convert_tab(self):
        """[NEW] 'Convert' tab - replaces the `convert` command."""
        page = self.make_page()

        card = Card(page)
        self.conv_amount = Field(card, value="1", hint="Enter an amount")         
        row, self.conv_from, self.conv_to = self.make_picker_row(card, "FROM", "TO")  
        self.conv_button = FlatButton(card, "Convert")

        card.body.Add(make_label(card, "AMOUNT"), 0, wx.BOTTOM, 6)
        card.body.Add(self.conv_amount, 0, wx.EXPAND)
        card.body.AddSpacer(18)
        card.body.Add(row, 0, wx.EXPAND)
        card.body.AddSpacer(22)
        card.body.Add(self.conv_button, 0, wx.EXPAND)

        result_card, self.conv_result, self.conv_sub = self.make_result_card(page)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(card, 0, wx.EXPAND)
        sizer.AddSpacer(16)
        sizer.Add(result_card, 0, wx.EXPAND)
        page.SetSizer(sizer)

        self.conv_button.Bind(wx.EVT_BUTTON, self.on_convert)                
        self.conv_amount.text.Bind(wx.EVT_TEXT_ENTER, self.on_convert)        

    def build_rate_tab(self):
        """[NEW] 'Exchange Rate' tab - replaces the `rate` command."""
        page = self.make_page()

        card = Card(page)
        row, self.rate_from, self.rate_to = self.make_picker_row(card, "BASE CURRENCY", "TARGET CURRENCY")
        self.rate_button = FlatButton(card, "Get Rate")

        card.body.Add(row, 0, wx.EXPAND)
        card.body.AddSpacer(22)
        card.body.Add(self.rate_button, 0, wx.EXPAND)

        result_card, self.rate_result, self.rate_sub = self.make_result_card(page)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(card, 0, wx.EXPAND)
        sizer.AddSpacer(16)
        sizer.Add(result_card, 0, wx.EXPAND)
        page.SetSizer(sizer)

        self.rate_button.Bind(wx.EVT_BUTTON, self.on_get_rate)

    def build_list_tab(self):
        """[NEW] 'Currencies' tab - replaces the `list` command."""
        page = self.make_page()

        card = Card(page)
        self.list_search = Field(card, hint="Search by code or name…")
        self.currency_list = CurrencyListBox(card)           

        card.body.Add(self.list_search, 0, wx.EXPAND)
        card.body.AddSpacer(14)
        card.body.Add(self.currency_list, 1, wx.EXPAND)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(card, 1, wx.EXPAND)
        sizer.AddSpacer(8)
        page.SetSizer(sizer)

        self.list_search.text.Bind(wx.EVT_TEXT, self.on_list_filter)

    # -------------------------------------------------------------------------
    # LOADING CURRENCIES (startup)
    # -------------------------------------------------------------------------

    def on_currencies_loaded(self, currencies):
        """[NEW] Called when get_currencies() finishes. Fills the pickers and the list tab."""
        self.currencies = currencies
        self.codes = [currency['code'] for _, currency in currencies]
        self.items = [(c['code'], c['name'], c.get('symbol', '')) for _, c in currencies]

        for picker in (self.conv_from, self.conv_to, self.rate_from, self.rate_to):
            picker.set_items(self.items)

        
        for picker, code in ((self.conv_from, "EUR"), (self.rate_from, "EUR"),
                             (self.conv_to, "USD"), (self.rate_to, "USD")):
            picker.set_code(code if code in self.codes else self.codes[0])

        self.fill_currency_list()
        self.set_status(f"{len(self.codes)} currencies loaded.", SUCCESS)

    def fill_currency_list(self, query=""):
        """[NEW] Replaces print_currencies(): shows code / name / symbol in the list tab."""
        query = query.strip().lower()
        shown = [i for i in self.items if query in i[0].lower() or query in i[1].lower()]
        self.currency_list.set_items(shown)

    def on_list_filter(self, event):
        """[STYLE] Live search in the Currencies tab."""
        self.fill_currency_list(self.list_search.GetValue())

    def on_load_error(self, error):
        """[NEW] Shown if the API can't be reached at startup."""
        self.set_status("Could not load currencies.", ERROR)
        wx.MessageBox(f"Could not load currencies:\n{error}", "Error", wx.OK | wx.ICON_ERROR)

    # -------------------------------------------------------------------------
    # EVENT HANDLERS (what happens when buttons are clicked)
    # -------------------------------------------------------------------------

    # ---- Convert tab ----
    def on_convert(self, event):
        """[NEW] Replaces the 'convert' branch of main()."""
        currency1 = self.conv_from.get_code()
        currency2 = self.conv_to.get_code()

        if not currency1 or not currency2:
            wx.MessageBox("Please choose both currencies.", "Missing input", wx.OK | wx.ICON_WARNING)
            return

        try:
            amount = float(self.conv_amount.GetValue())     
        except ValueError:
            wx.MessageBox("Invalid amount.", "Missing input", wx.OK | wx.ICON_WARNING)
            return

        self.conv_button.set_enabled(False)                 
        self.conv_button.set_label("Converting…")
        self.conv_result.SetLabel(" ")
        self.conv_sub.SetLabel(" ")
        self.set_status("Converting...")

        run_in_background(
            lambda: convert(currency1, currency2, amount),  
            lambda result: self.on_convert_done(result, currency1, currency2, amount),
            self.on_convert_error,
        )

    def on_convert_done(self, result, currency1, currency2, amount):
        self.conv_button.set_enabled(True)
        self.conv_button.set_label("Convert")
        if result is None:
            self.conv_result.SetForegroundColour(ERROR)
            self.conv_result.SetLabel("No rate available")
            self.conv_sub.SetLabel(f"Could not get a rate for {currency1} → {currency2}")
            self.set_status("Conversion failed.", ERROR)
            return
        self.conv_result.SetForegroundColour(ACCENT2)
        self.conv_result.SetLabel(f"{result:,.2f} {currency2}")
        if amount:
            self.conv_sub.SetLabel(f"{amount:,.2f} {currency1}  •  1 {currency1} = {result / amount:,.4f} {currency2}")
        else:
            self.conv_sub.SetLabel(f"{amount:,.2f} {currency1}")
        self.set_status("Done.", SUCCESS)

    def on_convert_error(self, error):
        self.conv_button.set_enabled(True)
        self.conv_button.set_label("Convert")
        self.set_status("Conversion failed.", ERROR)
        wx.MessageBox(f"Something went wrong:\n{error}", "Error", wx.OK | wx.ICON_ERROR)

    # ---- Rate tab ----
    def on_get_rate(self, event):
        """[NEW] Replaces the 'rate' branch of main()."""
        currency1 = self.rate_from.get_code()
        currency2 = self.rate_to.get_code()

        if not currency1 or not currency2:
            wx.MessageBox("Please choose both currencies.", "Missing input", wx.OK | wx.ICON_WARNING)
            return

        self.rate_button.set_enabled(False)
        self.rate_button.set_label("Fetching…")
        self.rate_result.SetLabel(" ")
        self.rate_sub.SetLabel(" ")
        self.set_status("Fetching rate...")

        run_in_background(
            lambda: exchange_rate(currency1, currency2),   
            lambda rate: self.on_rate_done(rate, currency1, currency2),
            self.on_rate_error,
        )

    def on_rate_done(self, rate, currency1, currency2):
        self.rate_button.set_enabled(True)
        self.rate_button.set_label("Get Rate")
        if rate is None:
            self.rate_result.SetForegroundColour(ERROR)
            self.rate_result.SetLabel("No rate available")
            self.rate_sub.SetLabel(f"Could not get a rate for {currency1} → {currency2}")
            self.set_status("Failed.", ERROR)
            return
        self.rate_result.SetForegroundColour(ACCENT2)
        self.rate_result.SetLabel(f"1 {currency1} = {rate:,.4f} {currency2}")
        if rate:
            self.rate_sub.SetLabel(f"1 {currency2} = {1 / rate:,.4f} {currency1}")
        self.set_status("Done.", SUCCESS)

    def on_rate_error(self, error):
        self.rate_button.set_enabled(True)
        self.rate_button.set_label("Get Rate")
        self.set_status("Failed.", ERROR)
        wx.MessageBox(f"Something went wrong:\n{error}", "Error", wx.OK | wx.ICON_ERROR)


# =============================================================================
# SECTION 7: START THE APP
# =============================================================================

if __name__ == "__main__":                                  
    app = wx.App()                                          
    frame = MainFrame()
    frame.Show()
    app.MainLoop()                                          
