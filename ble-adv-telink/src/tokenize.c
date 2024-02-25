#include <stdarg.h>
#include <stdbool.h>
#include "tokenize.h"

#ifndef NULL
#define NULL    0
#endif

int c_isSeparator(const int c, char* separator, bool spaces)
{
    if (separator)
    {
        for (; *separator; separator++)
        {
            if (c == *separator)
                return 1;
        }
    }
    if (!spaces)
        return 0;
	switch (c)
	{ /* in the "C" locale: */
		case ' ': /* space */
		case '\f': /* form feed */
		case '\n': /* new-line */
		case '\r': /* carriage return */
		case '\t': /* horizontal tab */
		case '\v': /* vertical tab */
			return 1;
		default:
			return 0;
	}
}

// std
int	c_isdigit(int c)
{
	if (c >= '0' && c <= '9')
		return (1);
	else
		return (0);
}

#define NEXTCHAR (PointBuf++)
#define CURCHAR (buff[PointBuf])
int tokenize(const char* buff, char* format, char* separator, bool strict_number, bool spaces, bool complete, ...)
{
	int count = 0;
    int PointBuf = 0;
	int PointFt = 0;

	va_list ap;
	va_start(ap, complete);
	while (format && format[PointFt]) // Read format
	{
		if (format[PointFt] == '%')
		{
			PointFt++;
			// for %*
			bool save = true;
			if (format[PointFt] == '*')
			{
				save = false;
				PointFt++;
			}
			// for %1234567890
			unsigned len = 0;
			bool lenEn = false;
			while (c_isdigit(format[PointFt]))
			{
				lenEn = true;
				len *= 10;
				len += (format[PointFt] - '0');
				PointFt++;
			}
			// for %[]
			char stop[LENSCANS];
			unsigned stopN = 0;
			if (format[PointFt] == '[')
			{
				while (format[PointFt] != ']')
				{
					if (format[PointFt] != '[')
					{
						stop[stopN] = format[PointFt];
						stopN++;
					}
					PointFt++;
				}
			}
			// %?
			switch (format[PointFt])
			{
				case 'c':
					if (CURCHAR == 0)
                        break;
					while (c_isSeparator(CURCHAR, separator, spaces)) // ignore isspace (std)
						NEXTCHAR; //
					if (save)
						*(char*)va_arg(ap, char*) = CURCHAR;
					if (save) // ignore %* (std)
						count++;
					if (CURCHAR == 0)
                        break;
                    NEXTCHAR;
					break;
				case 'u':
				case 'd':
                {
					int sign = 1;
					if (CURCHAR == 0)
                        break;
					while (!c_isdigit(CURCHAR))
					{
						if (CURCHAR == '+' || CURCHAR == '-')
							if (CURCHAR == '-')
								//if(format[PointFt] != 'u') // ignore sign (no std)
									sign = -1;
                        if (strict_number && (CURCHAR != 0) && ! c_isSeparator(CURCHAR, separator, spaces))
                            break;
                        NEXTCHAR;
                        if (CURCHAR == 0)
                            break;
					}
					long value = 0;
					if (CURCHAR == 0)
                        break;
					while(c_isdigit(CURCHAR) && (lenEn != true || len > 0))
					{
						value *= 10;
						value += (int)(CURCHAR - '0');
						NEXTCHAR;
						len--;
					}
                    if (strict_number && (CURCHAR != 0) && ! c_isSeparator(CURCHAR, separator, spaces))
                        break;

					if (save)
						*(int*)va_arg(ap, int*) = value * sign;
					if (save) // ignore %* (std)
						count++;
					break;
                }
				case ']':
				case 's':
                {
					char* t = save ? va_arg(ap, char*) : NULL;

					if (CURCHAR == 0)
                        break;
					while (c_isSeparator(CURCHAR, separator, spaces)) // ignor isspace (std)
						NEXTCHAR; //
					if (CURCHAR == 0)
                        break;

					while (true)
					{
						bool con = false;
                        if (CURCHAR == 0)
                            break;
						if (stopN != 0)
						{
							bool invert = (stop[0] == '^');
							con = !invert;
							for (unsigned i = (invert ? 1 : 0); i < stopN; i++)
								if (stop[i] == CURCHAR)
								{
									con = invert;
									break;
								}

							if (con == true)
								break;
						}

                        if (CURCHAR == 0)
                            break;
						if (!c_isSeparator(CURCHAR, separator, spaces) || ((!con && stopN != 0) && (lenEn != true || len > 0)))
						{
							if (save)
								*t = CURCHAR;
							NEXTCHAR;
                            if (CURCHAR == 0)
                                break;
							t++;
							len--;
						}
						else
							break;
					}
					// add \0
					{
						if (save)
							*t = '\0';
						t++;
					}
					if (save) // ignore %* (std)
						count++;
					break;
                }
			}
		}
		//else  // drop char in buff (no std)
		//	NEXTCHAR; //
		PointFt++;
	}
	va_end(ap);
    while (c_isSeparator(CURCHAR, NULL, true)) // ignore isspace (std)
        NEXTCHAR; //
    if (complete && (CURCHAR != 0))
        count = -1;
	return count;
}
