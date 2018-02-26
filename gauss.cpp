#include <iostream>
using namespace std;
int main()
{
	int i, j, k, l;
	float array[10][10], ans[10], func[10] = {0}, xishu;
	const int M = 3, N = 3;
	for (i=0;i<M;i++)
	{
	  for (j=0;j<N;j++)
	    cin >> array[i][j];
	  cin >> ans[i];
	}
	int row = 0, col = 0;
	while (true)
	{
		for (j=col;j<N;j++)
		  for (i=row;i<M;i++)
			if (array[i][j])
			  goto doublebreak;//从上到下找到第一个非零元 
		doublebreak:
		if (j >= N) break;
		if (i != row)
		{ 
			for (k=j;k<N;k++)
			  swap(array[row][k], array[i][k]);//交换两行
			swap(ans[row], ans[i]);
		}
		  
		for (k=row+1;k<M;k++)
		{
			xishu = array[k][j] / array[row][j];
			for (l=j;l<N;l++)
			  array[k][l] -= xishu * array[row][l];//两行相减使得消去首项 
			ans[k] -= xishu * ans[row];
		}
		row ++; col ++;//继续下一行下一列 
	}
	for (i=M-1;i>=0;i--)
	{
		for (j=0;j<N;j++)
		  if (array[i][j]) break;
		if (j < N)
		{
			func[j] = ans[i] / array[i][j];//从最底一层层回代 
			for (k=i-1;k>=0;k--)
			  ans[k] -= array[k][j] * func[j];
		}
		//可令自由变量计0 
	}
	for (i=0;i<N;i++)
	{
	  //for (j=0;j<N;j++)
	    //cout << array[i][j] << " ";
	  cout << func[i] << " ";
	  //cout << endl;
	}
	return 0;
}
