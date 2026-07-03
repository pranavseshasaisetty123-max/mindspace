import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';

interface TagCount {
  tag: string;
  count: number;
}

interface TagPieChartProps {
  data: TagCount[];
}

const COLORS = ['#6366f1', '#10b981', '#f43f5e', '#eab308', '#a855f7', '#06b6d4', '#f97316'];

export const TagPieChart: React.FC<TagPieChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-xs text-gray-500 italic">
        No tags logged yet to map distribution.
      </div>
    );
  }

  // Filter top 7 tags to keep chart clean and legibility high
  const chartData = data.slice(0, 7);

  const renderCustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-darkcard/95 border border-darkborder rounded-xl p-3 shadow-md backdrop-blur-sm text-xs">
          <p className="text-gray-200 font-semibold mb-1">#{payload[0].name}</p>
          <p className="text-indigo-400 font-bold">
            Occurrences: <span className="text-gray-100">{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-64 min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={75}
            paddingAngle={4}
            dataKey="count"
            nameKey="tag"
          >
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} stroke="#111622" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip content={renderCustomTooltip} />
          <Legend 
            verticalAlign="bottom" 
            height={36} 
            iconSize={6} 
            iconType="circle"
            formatter={(value) => <span className="text-[10px] text-gray-400">#{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
