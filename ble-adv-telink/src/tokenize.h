#define LENSCANS 10
int c_isSeparator(const int c, char* separator, bool spaces);
int	c_isdigit(int c);
int tokenize(const char* buff, char* format, char* separator, bool spaces, bool complete, ...);
