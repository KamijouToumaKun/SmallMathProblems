#include <ctime>
#include <fstream>
using namespace std;
ifstream fin("sudoku.txt");
ofstream fout("result.txt");
struct sudoku
{
	int num;					//所填的数字，0为未填 
	bool occu[9];				//标记所在行列宫每个数字是否已经存在 
	int occunum;				//所在行列宫已经存在的数字个数 
}array[9][9];
const int rank[9][9] = 			//九宫分区 
{
	0,0,0,1,1,1,2,2,2,
	0,0,0,1,1,1,2,2,2,
	0,0,0,1,1,1,2,2,2,
	3,3,3,4,4,4,5,5,5,
	3,3,3,4,4,4,5,5,5,
	3,3,3,4,4,4,5,5,5,
	6,6,6,7,7,7,8,8,8,
	6,6,6,7,7,7,8,8,8,
	6,6,6,7,7,7,8,8,8,
};
void fillin(int i, int j, int n);//在指定位置填上指定的数，并且更新所在行列宫其他数字的候选范围 
bool onlynum();					 //唯一数法：当一个空位所在行列宫已经有8个数字用过了，则这个空位确定 
bool onlyoccu();				 //隐含唯一数法：当一个空位所在行或列或宫里只有它有可能填上一个数，则这个空位确定

int chain[81][2];				 //储存所有occunum为指定数字n的空位
int top;						 //chain储存总量
bool chainoccu(int n);			 //统计所有occunum为指定数字n的空位储存在chain中 
int temp[9];					 //储存C(top, 9-n)的所有组合种类
bool chainsear(int n, int index, int step);//产生chain中所有(9-n)元组
								 //若交集数量也为(9-n) 则擦除所同的行或列或宫中其他空位的这几个候选数 
int checksame(int n);			 //判断(9-n)元组的元素是否同行或列或宫
bool common[9];					 //储存chain中每一个(9-n)元组的候选数的交集

void suppose();					 //试数法 
clock_t start;					 //记录运行时间 

void fillin(int i, int j, int n)
{
	int k, l;
	array[i][j].num = n+1;
	array[i][j].occunum = 9;
	for (k=0;k<9;k++)//行列更新 
	{
	  	if (!array[i][k].num && !array[i][k].occu[n])
	  	{
			array[i][k].occu[n] = true;
			array[i][k].occunum ++;
	    }
		if (!array[k][j].num && !array[k][j].occu[n])
	  	{
			array[k][j].occu[n] = true;
			array[k][j].occunum ++;
	    }
	}
	for (k=0;k<9;k++)//九宫更新
	  for (l=0;l<9;l++)
	    if (rank[k][l] == rank[i][j] && !array[k][l].num
			&& !array[k][l].occu[n])
		{
			array[k][l].occu[n] = true;
			array[k][l].occunum ++;
		}
}

bool onlynum()
{
	int i, j, k, l;
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	    if (array[i][j].occunum == 8)
	    {
	    	for (k=0;k<9;k++)
	    	  if (!array[i][j].occu[k]) break;
	    	fillin(i, j, k);
			return true;
		}
	return false;
}

bool onlyoccu()
{
	int i, j, k, l, n, num1, num2;
	for (n=0;n<9;n++)//待检验的数字 
	{
		for (i=0;i<9;i++)//每一行
		{
			num1 = -1;
			for (j=0;j<9;j++)
			  if (!array[i][j].num && !array[i][j].occu[n])
			  {
			  	  if (num1 < 0) num1 = j;
			  	  else break;
			  }
			if (num1 > 0 && j == 9)//判断是否恰有一个 
			{
				fillin(i, num1, n);
				return true;
			}
		}
		for (j=0;j<9;j++)//每一列 
		{
			num1 = -1;
			for (i=0;i<9;i++)
			  if (!array[i][j].num && !array[i][j].occu[n])
			  {
			  	  if (num1 < 0) num1 = i;
			  	  else break;
			  }
			if (num1 > 0 && i == 9)
			{
				fillin(num1, j, n);
				return true;
			}
		}
		for (i=1;i<=3;i++)//每个九宫
		  for (j=1;j<=3;j++)
		  {
			  num1 = -1;
		  	  for (k=3*(i-1);k<3*i;k++)//遍历每一个九宫 
	        	for (l=3*(j-1);l<3*j;l++)
	        	  if (!array[k][l].num && !array[k][l].occu[n])
	        	  {
	        	  	  if (num1 < 0)
					  {
						  num1 = k;
						  num2 = l;
					  }
					  else goto squarewrong;
				  }
			  squarewrong:
	          if (num1 > 0 && k == 3*i)
			  {
				  fillin(num1, num2, n);
				  return true;
			  }
		  }
	}
	return false;
}

int checksame(int n)
{
	int i;
	for (i=0;i<8-n;i++)//同行 
	  if (chain[temp[i]][0] != chain[temp[i+1]][0]) break;
	if (i == 8-n) return 1;
	
	for (i=0;i<8-n;i++)//同列 
	  if (chain[temp[i]][1] != chain[temp[i+1]][1]) break;
	if (i == 8-n) return 2;
	
	for (i=0;i<8-n;i++)//同九宫 
	  if ( rank[chain[temp[i]][0]][chain[temp[i]][1]] != 
		  rank[chain[temp[i+1]][0]][chain[temp[i+1]][1]] ) break;
	if (i == 8-n) return 3;
	return 0;
}

bool chainsear(int n, int index, int step)
{
	int i, j, k, l, m, style, count;
	if (step == 9-n)
	{
		if (! (style = checksame(n))) return false;//要求同行或列或宫 
		for (i=0;i<9;i++) 
		{
			common[i] = false;
			for (j=0;j<9-n;j++)
		      common[i] = common[i] ||
			  	!array[chain[temp[j]][0]][chain[temp[j]][1]].occu[i];
		}//求交集 
		count = 0;
		for (i=0;i<9;i++)
		  if (common[i]) count ++;
		if (count == 9-n)//交集元素也恰有(9-n)个 
		{
			bool flag = false;
			switch (style)
			{
				case 1://同行 
					for (i=0;i<9;i++)
					{
						if (array[chain[temp[0]][0]][i].num) continue;
						for (j=0;j<9-n;j++)
						  if (i == chain[temp[j]][1]) break;
						if (j == 9-n)//判断是所同的行或列或宫中其他空位
						{
							for (j=0;j<9;j++)
							  if (common[j] && !array[chain[temp[0]][0]][i].occu[j])
							  {//可擦除的候选数尚未擦除 
							  	  flag = true;
							  	  array[chain[temp[0]][0]][i].occu[j] = true;
							  	  array[chain[temp[0]][0]][i].occunum ++;
							  }
						}
					}break;
				case 2://同列 
					for (i=0;i<9;i++)
					{
						if (array[i][chain[temp[0]][1]].num) continue;
						for (j=0;j<9-n;j++)
						  if (i == chain[temp[j]][0]) break;
						if (j == 9-n)
						{
							for (j=0;j<9;j++)
							  if (common[j] && !array[i][chain[temp[0]][1]].occu[j])
							  {
							  	  flag = true;
							  	  array[i][chain[temp[0]][1]].occu[j] = true;
							  	  array[i][chain[temp[0]][1]].occunum ++;
							  }
						}
					}break;
				case 3://同九宫 
					i = rank[chain[temp[0]][0]][chain[temp[0]][1]] / 3 + 1;
					j = rank[chain[temp[0]][0]][chain[temp[0]][1]] % 3 + 1;
					for (k=3*(i-1);k<3*i;k++)//遍历九宫 
	        		  for (l=3*(j-1);l<3*j;l++)
					  {
						  if (array[k][l].num) continue;
						  for (m=0;m<9-n;m++)
						    if (k == chain[temp[m]][0] && l == chain[temp[m]][1])
							  break;
						  if (m == 9-n)
						  {
							for (m=0;m<9;m++)
							  if (common[m] && !array[k][l].occu[m])
							  {
							  	  flag = true;
							  	  array[k][l].occu[m] = true;
							  	  array[k][l].occunum ++;
							  }
						}
					  }break;
			}
			return flag;
		}
		else return false;//要有所作为才返回true 
	}
	else
	{
		for (i=index;i<top+n-8+step;i++)//递归构造(9-n)元组 
		{
			temp[step] = i;
			if (chainsear(n, i+1, step+1)) return true;//有一组成功就返回true并暂时停止 
		}
		return false;
	}
}

bool chainoccu(int n)
{
	int i, j;
	top = 0;
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	    if (!array[i][j].num && array[i][j].occunum >= n)
	    {
			chain[top][0] = i;
			chain[top][1] = j;
			top ++;
		}
	if (top >= 9-n) return chainsear(n, 0, 0);
	else return false;
}

void suppose()
{
	int i, j, k, l, m, n;
	for (i=0;i<9;i++)//找到第一个空位 
	  for (j=0;j<9;j++)
	    if (!array[i][j].num)
		  goto supposeblank;
	supposeblank:
	if (i == 9)//没有空位，全部假设成立 
	{
		for (i=0;i<9;i++)//输出 
		{
			for (j=0;j<9;j++)
			  fout << array[i][j].num << " ";
			fout << endl;
		}
		fout << "Time: " << clock()-start << "ms." << endl;
		exit(0);//有解即唯一解，结束程序 
		//可以在这里不停止程序，但将空位排序后再递归搜索，这样可以防止重复地寻找多解 
	}
	
	sudoku t[9][9];
	for (k=0;k<9;k++)
	  for (l=0;l<9;l++)
	    t[k][l] = array[k][l];//备份 
	for (k=0;k<9;k++)
	  if (!array[i][j].occu[k])
	  {
	  	  fillin(i, j, k);//在空位试填候选数 
		  while ( onlynum() || onlyoccu()//反复使用其他方法直到全无效果 
			|| chainoccu(7) ) ;
	  	  for (l=0;l<9;l++)
	  	    for (m=0;m<9;m++)
	  	      if (!array[l][m].num)
	  	      {
	  	      	  for (n=0;n<9;n++)
	  	      	    if (!array[l][m].occu[n]) break;
	  	      	  if (n == 9)//有空位没有一个候选数，即假设不成立 
					goto supposewrong;
			  }
		  suppose();//暂时没有矛盾，递归找下一个空位 
		  supposewrong:
		  for (l=0;l<9;l++)
	  	    for (m=0;m<9;m++)
	  	      array[l][m] = t[l][m];//复制回来，尝试下一种可能 
	  }
}

int main()
{
	start = clock();
	int i, j, k, l;
	
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	  {
	  	  fin >> array[i][j].num;
	  	  for (k=0;k<9;k++)
	  	    array[i][j].occu[k] = false;
	  	  array[i][j].occunum = 0;
	  }
	for (i=0;i<9;i++)
	  for (j=0;j<9;j++)
	  {
	  	  if (array[i][j].num) array[i][j].occunum = 9;
	  	  else//读入与统计各空位的occu 
	  	  {
			  for (k=0;k<9;k++)//行列 
			  {
			  	  if (array[i][k].num)
					array[i][j].occu[array[i][k].num-1] = true;
			  	  if (array[k][j].num)
					array[i][j].occu[array[k][j].num-1] = true;
			  }
			  for (k=0;k<9;k++)//九宫
			    for (l=0;l<9;l++)
			      if (rank[k][l] == rank[i][j] && array[k][l].num)
				    array[i][j].occu[array[k][l].num-1] = true;
			  for (k=0;k<9;k++)//统计occunum 
				if (array[i][j].occu[k])
				  array[i][j].occunum ++;
		  }
	  }
	while ( onlynum() || onlyoccu()//反复使用以上方法直到全无效果 
		|| chainoccu(7) ) ;
	suppose();
	return 0;
}
