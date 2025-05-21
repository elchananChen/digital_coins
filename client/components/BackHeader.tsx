import React from 'react';
import { TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '@/utils/Themes/ThemeProvider';
import { Box } from './ui/box';
import { Text } from './ui/text';

interface BackHeaderProps {
  title?: string;
  icons?: string[];
  onPressIcons?: Function[];
  bgColor?: 'transparent' | 'white' | 'black';
  colorScheme?: 'alwaysWhite' | 'themeBased';
}

function BackHeader({
  title,
  icons,
  onPressIcons,
  bgColor = 'transparent',
  colorScheme = 'themeBased',
}: BackHeaderProps) {
  const navigation = useNavigation();
  const { appliedTheme } = useTheme();

  // Determine the background class based on the bgColor prop
  const getBgClass = () => {
    switch (bgColor) {
      case 'white':
        return 'bg-white';
      case 'black':
        return 'bg-black';
      default:
        return 'bg-transparent';
    }
  };

  // Determine the arrow icon and text color based on the colorScheme prop
  const isWhite = colorScheme === 'alwaysWhite';

  const textColor = isWhite ? 'text-white' : `text-text-${appliedTheme}`;

  return (
    <Box className={`mb-[1rem] p-4 ${getBgClass()} relative flex-row items-center justify-between`}>
      {/* Centered Title */}
      <Box className="flex-1 items-center justify-center">
        <Text className={`font-bold ${textColor} text-center text-xl`}>{title || ''}</Text>
      </Box>
      {/* Right Icons */}
      <Box className="absolute right-4 flex-row items-center gap-2">
        {icons?.map((icon, index) => (
          <TouchableOpacity key={icon} onPress={() => onPressIcons?.[index]?.()}>
            <Text>{icon}</Text>
          </TouchableOpacity>
        ))}
      </Box>
    </Box>
  );
}

export default BackHeader;
