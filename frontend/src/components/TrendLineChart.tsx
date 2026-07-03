import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

interface TrendData {
  date: string;
  avg_mood: number;
  avg_stress: number;
  avg_energy: number;
  avg_sleep: number;
}

interface TrendLineChartProps {
  data: TrendData[];
  activeMetric: 'avg_mood' | 'avg_stress' | 'avg_energy' | 'avg_sleep';
}

const METRIC_CONFIGS = {
  avg_mood: { label: 'Mood Index', color: '#6366f1', gradient: 'colorMood' },
  avg_stress: { label: 'Stress Level', color: '#f43f5e', gradient: 'colorStress' },
  avg_energy: { label: 'Energy Level', color: '#10b981', gradient: 'colorEnergy' },
  avg_sleep: { label: 'Sleep Hours', color: '#eab308', gradient: 'colorSleep' }
};

export const TrendLineChart: React.FC<TrendLineChartProps> = ({ data, activeMetric }) => {
  const config = METRIC_CONFIGS[activeMetric];

  // Custom tooltips matched to MindSpace premium dark slate theme
  const renderCustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-darkcard/95 border border-darkborder rounded-xl p-3 shadow-md backdrop-blur-sm text-xs">
          <p className="text-gray-400 font-semibold mb-1">{payload[0].payload.date}</p>
          <p style={{ color: config.color }} className="font-bold">
            {config.label}: <span className="text-gray-100">{payload[0].value}</span>
          </p>
        </div>
      );
    }
    return null;
  };

  // Adjust Y-axis scale domain depending on the active metric type
  const domain = (activeMetric === 'avg_sleep' ? [0, 'auto'] : [1, 5]) as any;

  return (
    <div className="w-full h-80 min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id={config.gradient} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={config.color} stopOpacity={0.15}/>
              <stop offset="95%" stopColor={config.color} stopOpacity={0.0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} opacity={0.2} />
          <XAxis 
            dataKey="date" 
            stroke="#6b7280" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false} 
            dy={10}
          />
          <YAxis 
            stroke="#6b7280" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false} 
            domain={domain}
            allowDecimals={true}
            dx={-5}
          />
          <Tooltip content={renderCustomTooltip} />
          <Area 
            type="monotone" 
            dataKey={activeMetric} 
            stroke={config.color} 
            strokeWidth={2}
            fillOpacity={1} 
            fill={`url(#${config.gradient})`} 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
