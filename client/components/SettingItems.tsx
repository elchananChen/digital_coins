import React from 'react';
import { Text } from 'react-native';
import { Box } from '@/components/ui/box';
import { Icon } from '@/components/ui/icon';
import { ChevronRight } from 'lucide-react-native';
import { IC_ChevronRight, IC_ChevronRight_White } from '@/utils/constants/Icons';
import { useTheme } from '@/utils/Themes/ThemeProvider';

interface SettingItemProps {
  title: string;
  IconComponent?: React.ElementType;
  badge?: string;
}

const SettingItem: React.FC<SettingItemProps> = ({ title, IconComponent, badge }) => {
  const { appliedTheme } = useTheme();
  return (
    <Box className="flex flex-row items-center">
      <Box className="flex-1 flex-row items-center gap-3">
        <Box className="rounded-full p-2">
          {IconComponent && <IconComponent className="h-12 w-12" />}
        </Box>
        <Text className={`text-text-${appliedTheme} text-[17px] font-medium`}>{title}</Text>
      </Box>
      <Box className="ml-auto">
        <Box className="flex flex-row items-center justify-center gap-1 ">
          {badge && (
            <Box className={`bg-badge-${appliedTheme} rounded-full p-1`}>
              <Text className="ml-1 mr-1 text-[13px] text-purple-500">{badge}</Text>
            </Box>
          )}
          {appliedTheme === 'dark' ? (
            <IC_ChevronRight_White className="h-4 w-4" />
          ) : (
            <IC_ChevronRight className="h-4 w-4" />
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default SettingItem;
