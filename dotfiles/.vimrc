set nocompatible " Never allow compatibility mode with vi

" Vundle and plugins
filetype off " Required for Vundle

" Set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim
call vundle#begin()

" Let Vundle manage Vundle
Bundle "gmarik/vundle"

" Hybrid for syntax highlighting
Bundle 'w0ng/vim-hybrid'

" Airline instead of powerline because it's faster
Plugin 'vim-airline/vim-airline'
Plugin 'vim-airline/vim-airline-themes'
let g:airline_powerline_fonts = 1
let g:airline_theme='powerlineish'
set timeoutlen=50 " Makes the switch from insert to normal look faster
set noshowmode " Airline will take care of telling us the mode
set laststatus=2 " Always show airline

" Syntax highlighting groups
Plugin 'toyamarinyon/vim-swift'
Plugin 'tmux-plugins/vim-tmux'

" Work better with tmux
Plugin 'christoomey/vim-tmux-navigator'

" Work better with git
Plugin 'tpope/vim-fugitive'

" Work better with syntax checking
Plugin 'scrooloose/syntastic'
let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 0
let g:syntastic_check_on_open = 0
let g:syntastic_check_on_wq = 0

" Swift support
Plugin 'jph00/swift-apple'

" Done with Vundle and bundles
call vundle#end()
filetype plugin indent on

" Set up colors
set t_Co=256
set bg=dark
hi Normal guibg=black guifg=white
colorscheme hybrid
syntax enable

" Window display
set showcmd " Display incomplete commands
set splitright " Split new vertical windows right of current window
set splitbelow " Split new horizontal windows below current window
set winminheight=0 " Allow windows to shrink to status line
set winminwidth=0 " Allow windows to shrink to vertical separator

" Edit field display
set number "Display line numbers
set numberwidth=4 " Minimum number of columns to show for line numbers
set wrap " Wrap lines
set lbr " Wrap lines on word boundaries
set list " Show whitespace characters
set listchars=tab:»\ ,trail:· " Show tabs and trailing spaces
set whichwrap+=<,>,[,] " Allow arrow keys to wrap lines

" Indenting
set autoindent " Copy indent from current line for new line
set nosmartindent " Don't right-shift lines
set expandtab " Insert spaces for <Tab> press; use spaces to indent
set smarttab " <Tab> respects 'shiftwidth', 'tabstop', 'softtabstop'
set tabstop=4 " Visible width of tabs
set softtabstop=4 " Edit as if tabs are 4 characters wide
set shiftwidth=4 " Number of spaces to use for indenting
set shiftround " Round indent to a multiple of 'shiftwidth'

" Searching
set incsearch " Do incremental searching (as you type)
set ignorecase " Don't care about case...
set smartcase " ...unless I use an uppercase letter
"set hlsearch " Highlight results

" Editing
set hidden " Hide buffers instead of closing them
set backspace=indent,eol,start " Fix backspacing
set updatecount=20 " Update swap file every 20 characters

"set modeline

" Autocommands to set up filetypes
"au BufNewFile,BufRead *tmux.conf* set filetype=tmux
"au BufNewFile,BufRead *gitconfig* set filetype=gitconfig

