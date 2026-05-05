import React, { useState } from 'react';

export default function Tooltip({
  children,
  text,
  position = 'top',
  backgroundColor = '#2b2d30ff'
}) {
  const [isVisible, setIsVisible] = useState(false);

  const getTooltipPosition = () => {
    switch (position) {
      case 'top':
        return { bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' };
      case 'bottom':
        return { top: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' };
      case 'left':
        return { right: 'calc(100% + 8px)', top: '50%', transform: 'translateY(-50%)' };
      case 'right':
        return { left: 'calc(100% + 8px)', top: '50%', transform: 'translateY(-50%)' };
      default:
        return { bottom: 'calc(100% + 8px)', left: '50%', transform: 'translateX(-50%)' };
    }
  };

  const getArrowStyle = () => {
    const baseArrow = {
      position: 'absolute',
      width: 0,
      height: 0,
      border: '5px solid transparent'
    };

    switch (position) {
      case 'top':
        return {
          ...baseArrow,
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          borderTopColor: backgroundColor,
          borderBottom: 'none'
        };
      case 'bottom':
        return {
          ...baseArrow,
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          borderBottomColor: backgroundColor,
          borderTop: 'none'
        };
      case 'left':
        return {
          ...baseArrow,
          left: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          borderLeftColor: backgroundColor,
          borderRight: 'none'
        };
      case 'right':
        return {
          ...baseArrow,
          right: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          borderRightColor: backgroundColor,
          borderLeft: 'none'
        };
      default:
        return baseArrow;
    }
  };

  return (
    <div
      style={{
        position: 'relative',
        display: 'inline-block'
      }}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div
          style={{
            position: 'absolute',
            padding: '8px 12px',
            borderRadius: '6px',
            backgroundColor: backgroundColor,
            color: 'white',
            fontSize: '12px',
            whiteSpace: 'nowrap',
            zIndex: 10001,
            pointerEvents: 'none',
            ...getTooltipPosition()
          }}
        >
          {text}
          <div style={getArrowStyle()} />
        </div>
      )}
    </div>
  );
}